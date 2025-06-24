import uuid
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models import Task, TaskStatus, TaskPriority
from src.schemas import TaskCreate, TaskFilter
from datetime import datetime, timezone


async def create_task(session: AsyncSession, data: TaskCreate) -> Task:
    """Создать новую задачу."""
    task = Task(
        id=uuid.uuid4(),
        title=data.title,
        description=data.description,
        priority=TaskPriority[data.priority],
        status=TaskStatus.NEW,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def get_task(session: AsyncSession, task_id: uuid.UUID) -> Optional[Task]:
    """Получить задачу по id."""
    result = await session.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def filter_tasks(session: AsyncSession, filters: TaskFilter) -> Sequence[Task]:
    """Получить список задач с фильтрацией и пагинацией."""
    stmt = select(Task)
    if filters.status:
        stmt = stmt.where(Task.status == TaskStatus[filters.status])
    if filters.priority:
        stmt = stmt.where(Task.priority == TaskPriority[filters.priority])
    stmt = stmt.offset(filters.skip).limit(filters.limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def cancel_task(session: AsyncSession, task_id: uuid.UUID) -> Optional[Task]:
    """
    Отменить задачу, если она в статусе NEW, PENDING или IN_PROGRESS.
    Возвращает обновлённую задачу или None, если не найдена.
    """
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return None
    if task.status not in [TaskStatus.NEW, TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
        return task
    task.status = TaskStatus.CANCELLED
    task.finished_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(task)
    return task
