import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("OCMS_DATABASE_URL", "postgresql+psycopg://ocms:ocms_local@localhost:5432/ocms")
os.environ.setdefault("OCMS_AWS_REGION", "us-east-1")

from ocms.main import app  # noqa: E402


@pytest.mark.asyncio
async def test_health_returns_ok() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
