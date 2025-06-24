import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Убираем ручное добавление sys.path, так как pytest.ini уже настроен
from main import app
from core.db import get_async_session
from models import Base

# Настройка тестовой базы данных
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Создание тестового движка
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    test_engine, expire_on_commit=False, class_=AsyncSession
)


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для всей сессии тестов"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Создание таблиц в тестовой базе данных"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для создания сессии базы данных для каждого теста"""
    async with TestSessionLocal() as session:
        yield session


async def override_get_async_session():
    """Переопределение зависимости для получения тестовой сессии"""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def async_client(
    async_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для создания HTTP клиента для тестирования FastAPI приложения"""
    # Переопределяем зависимость базы данных
    app.dependency_overrides[get_async_session] = override_get_async_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    # Очищаем переопределения после теста
    app.dependency_overrides.clear()
