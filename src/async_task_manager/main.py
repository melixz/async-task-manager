import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from async_task_manager.api import health_router, task_router
from async_task_manager.core.rabbitmq import rabbitmq_manager

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


app = FastAPI(
    title="Async Task Manager",
    description="""
## Асинхронный сервис управления задачами

Сервис для создания и обработки задач в асинхронном режиме с поддержкой:

* **Создание задач** через REST API
* **Асинхронная обработка** в фоновом режиме
* **Система приоритетов** (LOW, MEDIUM, HIGH)
* **Статусная модель** (NEW, PENDING, IN_PROGRESS, COMPLETED, FAILED, CANCELLED)
* **Фильтрация и пагинация** результатов
* **Мониторинг состояния** сервиса

### Технологии
- **Python 3.12+** с FastAPI
- **PostgreSQL 14+** для хранения данных
- **RabbitMQ** для очереди задач
- **SQLAlchemy** ORM с Alembic миграциями
- **AsyncPG** для асинхронного доступа к БД

### Статусы задач
- `NEW` - новая задача
- `PENDING` - ожидает обработки
- `IN_PROGRESS` - в процессе выполнения
- `COMPLETED` - завершено успешно
- `FAILED` - завершено с ошибкой
- `CANCELLED` - отменено
    """,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(task_router, prefix="/api/v1")
app.include_router(health_router)
