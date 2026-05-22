import os

import pytest

os.environ.setdefault(
    "OCMS_DATABASE_URL", "postgresql+psycopg://ocms:ocms_local@localhost:5432/ocms"
)
os.environ.setdefault("OCMS_AWS_REGION", "us-east-1")

from httpx import ASGITransport, AsyncClient  # noqa: E402

from ocms.main import app  # noqa: E402


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_job_logs_empty() -> None:
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
        response = await client.get(f"/jobs/{job_id}/logs")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
