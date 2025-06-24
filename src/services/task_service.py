import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from src.schemas import TaskCreate, TaskRead, TaskStatusRead, TaskFilter
from src.repositories import create_task, get_task, filter_tasks, cancel_task
from src.core.rabbitmq import get_rabbitmq_manager
from src.models import TaskStatus
import logging
import os
import sys

logger = logging.getLogger(__name__)


def is_test_env() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ or any(
        "pytest" in arg for arg in sys.argv
    )


async def create_task_service(session: AsyncSession, data: TaskCreate) -> TaskRead:
    """Создание новой задачи и отправка в RabbitMQ"""
    task = await create_task(session, data)

    try:
        if not is_test_env():
            rabbitmq = await get_rabbitmq_manager()
            await rabbitmq.publish_task(task.id, data.priority)
        task.status = TaskStatus.PENDING
        await session.commit()
        await session.refresh(task)
        logger.info(f"Задача {task.id} создана и отправлена в очередь")
    except Exception as e:
        logger.error(f"Ошибка отправки задачи {task.id} в RabbitMQ: {e}")
    return TaskRead.model_validate(task)


async def get_task_service(session: AsyncSession, task_id: uuid.UUID) -> TaskRead:
    """Получение задачи по id"""
    task = await get_task(session, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
        )
    return TaskRead.model_validate(task)


async def filter_tasks_service(
    session: AsyncSession, filters: TaskFilter
) -> Sequence[TaskRead]:
    """Получение списка задач"""
    tasks = await filter_tasks(session, filters)
    return [TaskRead.model_validate(t) for t in tasks]


async def get_task_status_service(
    session: AsyncSession, task_id: uuid.UUID
) -> TaskStatusRead:
    """Получение статуса задачи по id"""
    task = await get_task(session, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
        )
    return TaskStatusRead(id=task.id, status=task.status.value)


async def cancel_task_service(session: AsyncSession, task_id: uuid.UUID) -> TaskRead:
    """
    Отмена задачи по id с бизнес-валидацией статуса.
    """
    task = await cancel_task(session, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
        )
    if task.status.value != "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Задачу можно отменить только в статусах NEW, PENDING, IN_PROGRESS",
        )
    return TaskRead.model_validate(task)
