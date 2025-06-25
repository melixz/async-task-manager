import asyncio

import pytest


@pytest.mark.asyncio
async def test_priority_processing(async_client):
    payload_high = {"title": "high prio", "description": "high", "priority": "HIGH"}
    payload_low = {"title": "low prio", "description": "low", "priority": "LOW"}
    resp_high = await async_client.post("/api/v1/tasks/", json=payload_high)
    resp_low = await async_client.post("/api/v1/tasks/", json=payload_low)
    id_high = resp_high.json()["id"]
    id_low = resp_low.json()["id"]

    status_high, status_low = None, None
    for _ in range(30):
        s_high = await async_client.get(f"/api/v1/tasks/{id_high}/status")
        s_low = await async_client.get(f"/api/v1/tasks/{id_low}/status")
        status_high = s_high.json()["status"]
        status_low = s_low.json()["status"]
        if status_high in ("COMPLETED", "FAILED") and status_low in (
            "COMPLETED",
            "FAILED",
        ):
            break
        await asyncio.sleep(0.5)
    assert status_high == "COMPLETED"
    assert status_low == "COMPLETED"

    info_high = await async_client.get(f"/api/v1/tasks/{id_high}")
    info_low = await async_client.get(f"/api/v1/tasks/{id_low}")
    finished_high = info_high.json()["finished_at"]
    finished_low = info_low.json()["finished_at"]
    assert finished_high <= finished_low
