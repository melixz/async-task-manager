import pytest


@pytest.mark.asyncio
async def test_cancel_task(async_client):
    payload = {"title": "cancel test", "description": "cancel desc", "priority": "LOW"}
    response = await async_client.post("/api/v1/tasks/", json=payload)
    assert response.status_code == 201
    data = response.json()
    task_id = data["id"]

    cancel_resp = await async_client.delete(f"/api/v1/tasks/{task_id}")
    assert cancel_resp.status_code == 200
    cancel_data = cancel_resp.json()
    assert cancel_data["status"] == "CANCELLED"

    status_resp = await async_client.get(f"/api/v1/tasks/{task_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "CANCELLED"

    cancel_again = await async_client.delete(f"/api/v1/tasks/{task_id}")
    assert cancel_again.status_code == 400 or cancel_again.status_code == 409
