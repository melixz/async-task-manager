import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from src.schemas import TaskCreate, TaskRead, TaskStatusRead, TaskFilter
from src.repositories import create_task, get_task, filter_tasks


async def create_task_service(session: AsyncSession, data: TaskCreate) -> TaskRead:
    """Создание новой задачи"""
    task = await create_task(session, data)
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
