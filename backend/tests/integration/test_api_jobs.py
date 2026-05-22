import os
import uuid

import pytest

os.environ.setdefault(
    "OCMS_DATABASE_URL", "postgresql+psycopg://ocms:ocms_local@localhost:5432/ocms"
)
os.environ.setdefault("OCMS_AWS_REGION", "us-east-1")

from httpx import ASGITransport, AsyncClient  # noqa: E402

from ocms.main import app  # noqa: E402


@pytest.mark.integration
@pytest.mark.asyncio
async def test_post_job_returns_201(db_session) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/jobs",
            json={
                "model_id": "meta-llama/Llama-3.1-8B",
                "quant_method": "GPTQ",
                "bits": 4,
                "instance_type": "g5.xlarge",
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert "job_id" in data
    assert data["model_id"] == "meta-llama/Llama-3.1-8B"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_jobs_returns_list() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/jobs",
            json={
                "model_id": "Qwen/Qwen3-8B",
                "quant_method": "AWQ",
                "bits": 4,
                "instance_type": "g5.xlarge",
            },
        )
        response = await client.get("/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_job_by_id() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_response = await client.post(
            "/jobs",
            json={
                "model_id": "meta-llama/Llama-3.1-8B",
                "quant_method": "GPTQ",
                "bits": 4,
                "instance_type": "g5.xlarge",
            },
        )
        job_id = create_response.json()["job_id"]
        response = await client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["job_id"] == job_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_nonexistent_job_returns_404() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/jobs/{uuid.uuid4()}")
    assert response.status_code == 404
