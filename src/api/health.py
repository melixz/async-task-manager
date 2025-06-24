from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db import get_async_session
from src.core.rabbitmq import get_rabbitmq_manager
from fastapi import Depends, status

router = APIRouter()


"""Проверка состояния сервиса"""


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(session: AsyncSession = Depends(get_async_session)):
    try:
        await session.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    try:
        rabbitmq = await get_rabbitmq_manager()
        rabbitmq_ok = (
            rabbitmq.connection is not None and not rabbitmq.connection.is_closed
        )
    except Exception:
        rabbitmq_ok = False
    return {"database": db_ok, "rabbitmq": rabbitmq_ok, "status": db_ok and rabbitmq_ok}
