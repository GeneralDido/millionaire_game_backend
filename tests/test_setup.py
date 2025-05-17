# tests/test_setup.py
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Test that our test client works correctly by calling the health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
