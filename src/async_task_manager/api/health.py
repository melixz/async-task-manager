from textwrap import dedent

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from async_task_manager.core.db import get_async_session
from async_task_manager.core.rabbitmq import get_rabbitmq_manager
from async_task_manager.schemas import HealthStatus

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Проверка состояния сервиса",
    description=dedent(
        """
        Проверяет состояние всех критически важных компонентов сервиса:

        * **database** — подключение к PostgreSQL
        * **rabbitmq** — подключение к RabbitMQ
        * **status** — общий статус (true, если все компоненты работают)

        Возвращает HTTP 200 даже если некоторые компоненты недоступны.
        Для мониторинга следует проверять поле `status` в ответе.
        """
    ),
)
async def health_check(session: AsyncSession = Depends(get_async_session)):
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        from sqlalchemy.exc import SQLAlchemyError

        if isinstance(e, SQLAlchemyError):
            db_ok = False
        else:
            raise

    try:
        rabbitmq = await get_rabbitmq_manager()
        rabbitmq_ok = rabbitmq.connection is not None and not rabbitmq.connection.is_closed
    except Exception as e:
        import aio_pika

        if isinstance(e, aio_pika.exceptions.AMQPException):
            rabbitmq_ok = False
        else:
            raise
        rabbitmq_ok = False
    return {"database": db_ok, "rabbitmq": rabbitmq_ok, "status": db_ok and rabbitmq_ok}
