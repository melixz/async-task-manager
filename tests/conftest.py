# ruff: noqa: E402
import os

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"

os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["RABBITMQ_URL"] = "amqp://guest:guest@localhost:5672/"


import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.async_task_manager.core.db import get_async_session
from src.async_task_manager.main import app
from src.async_task_manager.models.task import Base

engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def create_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_session():
    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


async def override_get_async_session():
    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
async def async_client(async_session):
    app.dependency_overrides[get_async_session] = override_get_async_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
