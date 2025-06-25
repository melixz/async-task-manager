from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from src.async_task_manager.core.db import get_async_session
from src.async_task_manager.main import app
from tests.conftest import override_get_async_session


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP-клиент, работающий напрямую с приложением FastAPI."""

    app.dependency_overrides[get_async_session] = override_get_async_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
