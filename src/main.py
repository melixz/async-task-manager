from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api import task_router, health_router
from src.core.rabbitmq import rabbitmq_manager
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    try:
        await rabbitmq_manager.connect()
        logger.info("RabbitMQ подключен при старте приложения")
    except Exception as e:
        logger.error(f"Ошибка подключения RabbitMQ: {e}")

    yield

    try:
        await rabbitmq_manager.close()
        logger.info("RabbitMQ отключен при остановке приложения")
    except Exception as e:
        logger.error(f"Ошибка отключения RabbitMQ: {e}")


app = FastAPI(title="Async Task Manager", version="1.0.0", lifespan=lifespan)

app.include_router(task_router, prefix="/api/v1")
app.include_router(health_router)
