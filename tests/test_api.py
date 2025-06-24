import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "database" in data and "rabbitmq" in data and "status" in data


@pytest.mark.asyncio
async def test_create_and_get_task(async_client: AsyncClient):
    payload = {
        "title": "Тестовая задача",
        "description": "Описание для теста",
        "priority": "HIGH",
    }
    resp = await async_client.post("/api/v1/tasks/", json=payload)
    assert resp.status_code == 201
    task = resp.json()
    assert task["title"] == payload["title"]
    assert task["priority"] == payload["priority"]
    task_id = task["id"]

    resp = await async_client.get(f"/api/v1/tasks/{task_id}")
    assert resp.status_code == 200
    task2 = resp.json()
    assert task2["id"] == task_id

    resp = await async_client.get(f"/api/v1/tasks/{task_id}/status")
    assert resp.status_code == 200
    status_data = resp.json()
    assert status_data["id"] == task_id
    assert status_data["status"] in [
        "NEW",
        "PENDING",
        "IN_PROGRESS",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
    ]

    resp = await async_client.delete(f"/api/v1/tasks/{task_id}")
    assert resp.status_code == 200
    cancelled = resp.json()
    assert cancelled["status"] == "CANCELLED"
