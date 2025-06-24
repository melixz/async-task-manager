import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas import TaskCreate, TaskRead, TaskStatusRead, TaskFilter
from src.services import (
    create_task_service,
    get_task_service,
    filter_tasks_service,
    get_task_status_service,
)
from src.core.db import get_async_session

router = APIRouter(prefix="/tasks", tags=["tasks"])

"""Создание новой задачи"""


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task_endpoint(
    data: TaskCreate,
    session: AsyncSession = Depends(get_async_session),
):
    return await create_task_service(session, data)


"""Получение списка задач"""


@router.get("/", response_model=list[TaskRead])
async def list_tasks_endpoint(
    status_: str = Query(None, alias="status"),
    priority: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
):
    filters = TaskFilter(status=status_, priority=priority, skip=skip, limit=limit)
    return await filter_tasks_service(session, filters)


"""Получение задачи по id"""


@router.get("/{task_id}", response_model=TaskRead)
async def get_task_endpoint(
    task_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
):
    return await get_task_service(session, task_id)


"""Получение статуса задачи по id"""


@router.get("/{task_id}/status", response_model=TaskStatusRead)
async def get_task_status_endpoint(
    task_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
):
    return await get_task_status_service(session, task_id)
