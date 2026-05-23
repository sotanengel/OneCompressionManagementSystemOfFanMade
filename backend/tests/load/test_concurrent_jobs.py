"""
Load test: 10 concurrent job submissions must not produce DB connection errors.

Run with locust:
    locust -f tests/load/test_concurrent_jobs.py --headless -u 10 -r 10 \
        --run-time 30s --host http://localhost:8000

Or as a smoke test with concurrent httpx (used in CI with a real Postgres):
    pytest tests/load/test_concurrent_jobs.py -m load
"""

from __future__ import annotations

import concurrent.futures

import pytest
import requests

_JOB_PAYLOAD = {
    "model_id": "meta-llama/Llama-3.1-8B",
    "quant_method": "GPTQ",
    "bits": 4,
    "instance_type": "g5.xlarge",
    "region": "us-east-1",
    "spot": False,
    "max_runtime_hours": 1,
}

_CONCURRENCY = 10


def _submit_job(base_url: str) -> int:
    resp = requests.post(f"{base_url}/jobs", json=_JOB_PAYLOAD, timeout=10)
    return resp.status_code


@pytest.mark.load
def test_concurrent_job_submissions_no_db_errors(base_url: str = "http://localhost:8000") -> None:
    with concurrent.futures.ThreadPoolExecutor(max_workers=_CONCURRENCY) as pool:
        futures = [pool.submit(_submit_job, base_url) for _ in range(_CONCURRENCY)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    error_codes = [r for r in results if r == 500]
    assert not error_codes, f"Got {len(error_codes)} 500 errors out of {_CONCURRENCY} requests"

    success_codes = [r for r in results if r in (201, 402)]
    assert len(success_codes) == _CONCURRENCY, f"Expected all 201/402, got: {results}"


try:
    from locust import HttpUser, between, task

    class OcmsUser(HttpUser):
        wait_time = between(0.1, 0.5)

        @task
        def submit_job(self) -> None:
            self.client.post("/jobs", json=_JOB_PAYLOAD)

        @task
        def list_jobs(self) -> None:
            self.client.get("/jobs")

        @task
        def health_check(self) -> None:
            self.client.get("/health")

except ImportError:
    pass
