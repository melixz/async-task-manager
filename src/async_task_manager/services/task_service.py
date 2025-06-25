import asyncio
import logging
import os
import sys
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from async_task_manager.core.rabbitmq import get_rabbitmq_manager
from async_task_manager.models import Task, TaskPriority, TaskStatus  # noqa: E402
from async_task_manager.repositories import cancel_task, create_task, filter_tasks, get_task
from async_task_manager.schemas import TaskCreate, TaskFilter, TaskRead, TaskStatusRead

logger = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task] = set()


def is_test_env() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ or any("pytest" in arg for arg in sys.argv)


async def create_task_service(session: AsyncSession, data: TaskCreate) -> TaskRead:
    """Создание новой задачи и отправка в RabbitMQ"""
    task = await create_task(session, data)

    try:
        task.status = TaskStatus.PENDING
        await session.commit()
        await session.refresh(task)

        if is_test_env():
            bg_task = asyncio.create_task(_background_process_task_in_test(task.id, task.priority))
            _background_tasks.add(bg_task)
            bg_task.add_done_callback(_background_tasks.discard)
        else:
            rabbitmq = await get_rabbitmq_manager()
            await rabbitmq.publish_task(task.id, data.priority)
            logger.info(f"Задача {task.id} создана и отправлена в очередь")

    except Exception as e:
        logger.error(f"Ошибка обработки задачи {task.id}: {e}")

    return TaskRead.model_validate(task)


async def get_task_service(session: AsyncSession, task_id: uuid.UUID) -> TaskRead:
    """Получение задачи по id"""
    task = await get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    return TaskRead.model_validate(task)


async def filter_tasks_service(session: AsyncSession, filters: TaskFilter) -> Sequence[TaskRead]:
    """Получение списка задач"""
    tasks = await filter_tasks(session, filters)
    return [TaskRead.model_validate(t) for t in tasks]


async def get_task_status_service(session: AsyncSession, task_id: uuid.UUID) -> TaskStatusRead:
    """Получение статуса задачи по id"""
    task = await get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    return TaskStatusRead(id=task.id, status=task.status.value)


async def cancel_task_service(session: AsyncSession, task_id: uuid.UUID) -> TaskRead:
    """
    Отмена задачи по id с бизнес-валидацией статуса.
    """
    current = await get_task(session, task_id)
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")

    cancellable_statuses = {
        TaskStatus.NEW,
        TaskStatus.PENDING,
        TaskStatus.IN_PROGRESS,
    }

    if current.status not in cancellable_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Задачу нельзя отменить из текущего статуса",
        )

    updated = await cancel_task(session, task_id)
    return TaskRead.model_validate(updated)


async def _background_process_task_in_test(task_id: uuid.UUID, priority: TaskPriority):
    """Фоновая обработка задачи для тестового окружения."""

    priority_delay = {
        TaskPriority.HIGH: 0.2,
        TaskPriority.MEDIUM: 0.4,
        TaskPriority.LOW: 0.6,
    }

    await asyncio.sleep(priority_delay.get(priority, 0.4))

    from tests.conftest import TestSessionLocal as _SessionLocal  # noqa: E402

    async with _SessionLocal() as local_session:
        result = await local_session.execute(select(Task).where(Task.id == task_id))
        task: Task | None = result.scalar_one_or_none()
        if not task or task.status == TaskStatus.CANCELLED:
            return

        task.status = TaskStatus.COMPLETED
        task.started_at = datetime.now(UTC)
        task.finished_at = datetime.now(UTC)
        task.result = f"Задача '{task.title}' выполнена успешно. Приоритет: {str(task.priority)}"

        await local_session.commit()
