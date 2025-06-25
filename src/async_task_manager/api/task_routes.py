import uuid
from textwrap import dedent

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from async_task_manager.core.db import get_async_session
from async_task_manager.schemas import (
    ErrorDetail,
    PriorityLiteral,
    StatusLiteral,
    TaskCreate,
    TaskFilter,
    TaskRead,
    TaskStatusRead,
    ValidationError,
)
from async_task_manager.services import (
    cancel_task_service,
    create_task_service,
    filter_tasks_service,
    get_task_service,
    get_task_status_service,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "/",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создание новой задачи",
    description=dedent(
        """
        Создает новую задачу и отправляет ее в очередь для асинхронной обработки.

        **Параметры:**
        * **title** — название задачи (обязательно)
        * **description** — описание задачи (обязательно)
        * **priority** — приоритет задачи: LOW, MEDIUM или HIGH (обязательно)

        **Поведение:**
        1. Задача создается со **статусом** NEW
        2. Статус изменяется на PENDING
        3. Задача отправляется в RabbitMQ для обработки
        4. Возвращается созданная задача

        **Приоритеты влияют на скорость обработки:**
        * **HIGH** — высший приоритет, обрабатывается быстрее всего
        * **MEDIUM** — средний приоритет
        * **LOW** — низший приоритет, обрабатывается медленнее всего
        """
    ),
    responses={
        201: {"description": "Задача успешно создана", "model": TaskRead},
        422: {"description": "Ошибка валидации данных", "model": ValidationError},
    },
)
async def create_task_endpoint(
    data: TaskCreate,
    session: AsyncSession = Depends(get_async_session),
):
    return await create_task_service(session, data)


@router.get(
    "/",
    response_model=list[TaskRead],
    summary="Получение списка задач",
    description=dedent(
        """
        Возвращает список задач с возможностью **фильтрации** и **пагинации**.

        **Параметры фильтрации:**
        * **status** — фильтр по статусу (NEW, PENDING, IN_PROGRESS, COMPLETED, FAILED, CANCELLED)
        * **priority** — фильтр по приоритету (LOW, MEDIUM, HIGH)

        **Параметры пагинации:**
        * **skip** — количество пропускаемых записей (по умолчанию 0)
        * **limit** — максимальное количество записей в ответе (1-100, по умолчанию 10)

        **Примеры запросов:**
        * `GET /tasks` — все задачи (первые 10)
        * `GET /tasks?status=COMPLETED` — только завершённые задачи
        * `GET /tasks?priority=HIGH&limit=20` — задачи с высоким приоритетом (до 20 штук)
        * `GET /tasks?skip=20&limit=10` — задачи с 21-й по 30-ю
        """
    ),
    responses={
        200: {"description": "Список задач", "model": list[TaskRead]},
        422: {"description": "Ошибка валидации параметров", "model": ValidationError},
    },
)
async def list_tasks_endpoint(
    status_: StatusLiteral | None = Query(
        None,
        alias="status",
        description="Фильтр по статусу задачи",
        examples={"example": {"summary": "Статус", "value": "COMPLETED"}},
    ),
    priority: PriorityLiteral | None = Query(
        None,
        description="Фильтр по приоритету задачи",
        examples={"example": {"summary": "Приоритет", "value": "HIGH"}},
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Количество пропускаемых записей",
        examples={"example": {"summary": "Пропустить", "value": 0}},
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Максимальное количество записей (1-100)",
        examples={"example": {"summary": "Лимит", "value": 10}},
    ),
    session: AsyncSession = Depends(get_async_session),
):
    filters = TaskFilter(status=status_, priority=priority, skip=skip, limit=limit)
    return await filter_tasks_service(session, filters)


@router.get(
    "/{task_id}",
    response_model=TaskRead,
    summary="Получение задачи по ID",
    description=dedent(
        """
        Возвращает **полную информацию** о задаче по её уникальному идентификатору.

        **Параметры:**
        * **task_id** — UUID задачи

        **Возвращает:**
        * Полную информацию о задаче, включая статус, приоритет, времена *создания*, *начала* и *завершения*
        * Результат выполнения (если задача завершена успешно)
        * Информацию об ошибке (если задача завершена с ошибкой)
        """
    ),
    responses={
        200: {"description": "Информация о задаче", "model": TaskRead},
        404: {"description": "Задача не найдена", "model": ErrorDetail},
        422: {"description": "Некорректный формат UUID", "model": ValidationError},
    },
)
async def get_task_endpoint(
    task_id: uuid.UUID = Path(
        ...,
        description="UUID задачи",
        examples={
            "example": {
                "summary": "UUID задачи",
                "value": "b3b7c7e2-8c2e-4e2a-9c2e-7e2a8c2e4e2a",
            }
        },
    ),
    session: AsyncSession = Depends(get_async_session),
):
    return await get_task_service(session, task_id)


@router.get(
    "/{task_id}/status",
    response_model=TaskStatusRead,
    summary="Получение статуса задачи",
    description=dedent(
        """
        Возвращает **только статус** задачи по её ID — более легковесная операция, чем получение полной информации.

        **Параметры:**
        * **task_id** — UUID задачи

        **Возможные статусы:**
        * `NEW` — задача только создана
        * `PENDING` — ожидает обработки
        * `IN_PROGRESS` — в процессе выполнения
        * `COMPLETED` — успешно завершена
        * `FAILED` — завершена с ошибкой
        * `CANCELLED` — отменена пользователем

        **Использование:** идеально подходит для быстрой проверки статуса задачи без загрузки всех данных.
        """
    ),
    responses={
        200: {"description": "Статус задачи", "model": TaskStatusRead},
        404: {"description": "Задача не найдена", "model": ErrorDetail},
        422: {"description": "Некорректный формат UUID", "model": ValidationError},
    },
)
async def get_task_status_endpoint(
    task_id: uuid.UUID = Path(
        ...,
        description="UUID задачи",
        examples={
            "example": {
                "summary": "UUID задачи",
                "value": "b3b7c7e2-8c2e-4e2a-9c2e-7e2a8c2e4e2a",
            }
        },
    ),
    session: AsyncSession = Depends(get_async_session),
):
    return await get_task_status_service(session, task_id)


@router.delete(
    "/{task_id}",
    response_model=TaskRead,
    summary="Отмена задачи",
    description=dedent(
        """
        Отменяет выполнение задачи и устанавливает ей статус **CANCELLED**.

        **Параметры:**
        * **task_id** — UUID задачи для отмены

        **Ограничения:** задачу можно отменить **только** если она находится в одном из статусов:

        * `NEW` — только создана, ещё не обрабатывается
        * `PENDING` — ожидает обработки в очереди
        * `IN_PROGRESS` — в процессе выполнения

        **Нельзя** отменить задачи в статусах:

        * `COMPLETED` — уже успешно завершена
        * `FAILED` — уже завершена с ошибкой
        * `CANCELLED` — уже отменена

        **Поведение:**
        1. Проверяется существование задачи
        2. Проверяется возможность отмены (статус)
        3. Статус задачи изменяется на **CANCELLED**
        4. Устанавливается время завершения
        5. Возвращается обновлённая задача
        """
    ),
    responses={
        200: {"description": "Задача успешно отменена", "model": TaskRead},
        400: {"description": "Задачу нельзя отменить из текущего статуса", "model": ErrorDetail},
        404: {"description": "Задача не найдена", "model": ErrorDetail},
        422: {"description": "Некорректный формат UUID", "model": ValidationError},
    },
)
async def cancel_task_endpoint(
    task_id: uuid.UUID = Path(
        ...,
        description="UUID задачи для отмены",
        examples={
            "example": {
                "summary": "UUID задачи",
                "value": "b3b7c7e2-8c2e-4e2a-9c2e-7e2a8c2e4e2a",
            }
        },
    ),
    session: AsyncSession = Depends(get_async_session),
):
    return await cancel_task_service(session, task_id)
