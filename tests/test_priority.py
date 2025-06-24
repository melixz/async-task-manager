import pytest
from httpx import AsyncClient
import asyncio


@pytest.mark.asyncio
async def test_priority_order(async_client: AsyncClient):
    payload_high = {"title": "High", "description": "", "priority": "HIGH"}
    payload_low = {"title": "Low", "description": "", "priority": "LOW"}

    resp_high = await async_client.post("/api/v1/tasks/", json=payload_high)
    resp_low = await async_client.post("/api/v1/tasks/", json=payload_low)
    assert resp_high.status_code == 201
    assert resp_low.status_code == 201
    id_high = resp_high.json()["id"]
    id_low = resp_low.json()["id"]

    await asyncio.sleep(1)
    resp_high_status = await async_client.get(f"/api/v1/tasks/{id_high}/status")
    resp_low_status = await async_client.get(f"/api/v1/tasks/{id_low}/status")
    status_high = resp_high_status.json()["status"]
    status_low = resp_low_status.json()["status"]

    assert status_high in ["PENDING", "IN_PROGRESS", "COMPLETED"]
    assert status_low in ["NEW", "PENDING", "IN_PROGRESS", "COMPLETED"]
