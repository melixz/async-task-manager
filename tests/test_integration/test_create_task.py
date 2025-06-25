import asyncio

import pytest


@pytest.mark.asyncio
async def test_create_task(async_client):
    payload = {
        "title": "integration test",
        "description": "integration test desc",
        "priority": "HIGH",
    }
    response = await async_client.post("/api/v1/tasks/", json=payload)
    assert response.status_code == 201
    data = response.json()
    task_id = data["id"]
    assert data["status"] == "PENDING"

    for _ in range(20):
        status_resp = await async_client.get(f"/api/v1/tasks/{task_id}/status")
        assert status_resp.status_code == 200
        status = status_resp.json()["status"]
        if status in ("COMPLETED", "FAILED"):
            break
        await asyncio.sleep(0.5)
    assert status == "COMPLETED"
