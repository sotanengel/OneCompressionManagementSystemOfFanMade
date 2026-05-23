from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ocms.api.deps import get_db
from ocms.core.models import FeatureFlags, Job, JobStatus
from ocms.main import app


def _make_job(
    *,
    model_id: str = "meta-llama/Llama-3.1-8B",
    estimated_cost_usd: Decimal | None = None,
    actual_cost_usd: Decimal | None = None,
    created_at: datetime | None = None,
    status: JobStatus = JobStatus.COMPLETED,
) -> Job:
    return Job(
        job_id=uuid.uuid4(),
        model_id=model_id,
        quant_method="GPTQ",
        bits=4,
        instance_type="g5.xlarge",
        region="us-east-1",
        spot=False,
        max_runtime_hours=2,
        status=status,
        feature_flags=FeatureFlags(),
        created_at=created_at or datetime.now(UTC),
        estimated_cost_usd=estimated_cost_usd,
        actual_cost_usd=actual_cost_usd,
    )


@pytest.fixture()
def client():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestCostSummaryEndpoint:
    def test_returns_correct_structure(self, client: TestClient) -> None:
        now = datetime.now(UTC)
        llama = "meta-llama/Llama-3.1-8B"
        jobs = [
            _make_job(model_id=llama, actual_cost_usd=Decimal("10.00"), created_at=now),
            _make_job(model_id="Qwen/Qwen3-8B", actual_cost_usd=Decimal("8.00"), created_at=now),
        ]
        with patch("ocms.api.routers.cost.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.list_all.return_value = jobs
            resp = client.get("/cost/summary")

        assert resp.status_code == 200
        data = resp.json()
        assert "total_usd" in data
        assert "by_model" in data
        assert "budget_warning" in data

    def test_calculates_actual_cost_total(self, client: TestClient) -> None:
        now = datetime.now(UTC)
        jobs = [
            _make_job(actual_cost_usd=Decimal("10.00"), created_at=now),
            _make_job(actual_cost_usd=Decimal("5.50"), created_at=now),
        ]
        with patch("ocms.api.routers.cost.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.list_all.return_value = jobs
            resp = client.get("/cost/summary")

        assert float(resp.json()["total_usd"]) == pytest.approx(15.5)

    def test_falls_back_to_estimated_when_no_actual(self, client: TestClient) -> None:
        now = datetime.now(UTC)
        jobs = [
            _make_job(actual_cost_usd=Decimal("10.00"), created_at=now),
            _make_job(estimated_cost_usd=Decimal("8.00"), created_at=now),  # no actual
        ]
        with patch("ocms.api.routers.cost.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.list_all.return_value = jobs
            resp = client.get("/cost/summary")

        assert float(resp.json()["total_usd"]) == pytest.approx(18.0)

    def test_groups_by_model(self, client: TestClient) -> None:
        now = datetime.now(UTC)
        llama = "meta-llama/Llama-3.1-8B"
        jobs = [
            _make_job(model_id=llama, actual_cost_usd=Decimal("10.00"), created_at=now),
            _make_job(model_id=llama, actual_cost_usd=Decimal("5.00"), created_at=now),
            _make_job(model_id="Qwen/Qwen3-8B", actual_cost_usd=Decimal("8.00"), created_at=now),
        ]
        with patch("ocms.api.routers.cost.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.list_all.return_value = jobs
            resp = client.get("/cost/summary?group_by=model")

        by_model = resp.json()["by_model"]
        assert float(by_model["meta-llama/Llama-3.1-8B"]) == pytest.approx(15.0)
        assert float(by_model["Qwen/Qwen3-8B"]) == pytest.approx(8.0)

    def test_filters_week_period(self, client: TestClient) -> None:
        now = datetime.now(UTC)
        jobs = [
            _make_job(actual_cost_usd=Decimal("100.00"), created_at=now - timedelta(days=10)),
            _make_job(actual_cost_usd=Decimal("5.00"), created_at=now - timedelta(days=3)),
        ]
        with patch("ocms.api.routers.cost.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.list_all.return_value = jobs
            resp = client.get("/cost/summary?period=week")

        assert float(resp.json()["total_usd"]) == pytest.approx(5.0)

    def test_filters_month_period(self, client: TestClient) -> None:
        now = datetime.now(UTC)
        jobs = [
            _make_job(actual_cost_usd=Decimal("100.00"), created_at=now - timedelta(days=35)),
            _make_job(actual_cost_usd=Decimal("20.00"), created_at=now - timedelta(days=15)),
        ]
        with patch("ocms.api.routers.cost.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.list_all.return_value = jobs
            resp = client.get("/cost/summary?period=month")

        assert float(resp.json()["total_usd"]) == pytest.approx(20.0)

    def test_all_period_includes_everything(self, client: TestClient) -> None:
        now = datetime.now(UTC)
        jobs = [
            _make_job(actual_cost_usd=Decimal("100.00"), created_at=now - timedelta(days=35)),
            _make_job(actual_cost_usd=Decimal("20.00"), created_at=now - timedelta(days=15)),
        ]
        with patch("ocms.api.routers.cost.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.list_all.return_value = jobs
            resp = client.get("/cost/summary?period=all")

        assert float(resp.json()["total_usd"]) == pytest.approx(120.0)

    def test_budget_warning_true_above_50(self, client: TestClient) -> None:
        now = datetime.now(UTC)
        jobs = [
            _make_job(actual_cost_usd=Decimal("30.00"), created_at=now),
            _make_job(actual_cost_usd=Decimal("25.00"), created_at=now),
        ]
        with patch("ocms.api.routers.cost.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.list_all.return_value = jobs
            resp = client.get("/cost/summary")

        assert resp.json()["budget_warning"] is True

    def test_budget_warning_false_below_50(self, client: TestClient) -> None:
        now = datetime.now(UTC)
        jobs = [_make_job(actual_cost_usd=Decimal("10.00"), created_at=now)]
        with patch("ocms.api.routers.cost.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.list_all.return_value = jobs
            resp = client.get("/cost/summary")

        assert resp.json()["budget_warning"] is False

    def test_empty_jobs_returns_zero(self, client: TestClient) -> None:
        with patch("ocms.api.routers.cost.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.list_all.return_value = []
            resp = client.get("/cost/summary")

        data = resp.json()
        assert float(data["total_usd"]) == 0.0
        assert data["budget_warning"] is False
        assert data["by_model"] == {}


class TestBudgetLimit:
    def test_create_job_rejected_when_budget_exceeded(self, client: TestClient) -> None:
        now = datetime.now(UTC)
        expensive_jobs = [
            _make_job(actual_cost_usd=Decimal("60.00"), created_at=now),
            _make_job(actual_cost_usd=Decimal("45.00"), created_at=now),
        ]
        with patch("ocms.api.routers.jobs.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.list_all.return_value = expensive_jobs
            resp = client.post(
                "/jobs",
                json={
                    "model_id": "meta-llama/Llama-3.1-8B",
                    "quant_method": "GPTQ",
                    "bits": 4,
                    "instance_type": "g5.xlarge",
                    "region": "us-east-1",
                    "spot": False,
                    "max_runtime_hours": 2,
                },
            )

        assert resp.status_code == 402
        assert "budget" in resp.json()["detail"].lower()

    def test_create_job_succeeds_when_budget_not_exceeded(self, client: TestClient) -> None:
        now = datetime.now(UTC)
        cheap_jobs = [_make_job(actual_cost_usd=Decimal("10.00"), created_at=now)]
        new_job = _make_job(
            estimated_cost_usd=Decimal("2.00"),
            created_at=now,
            status=JobStatus.PENDING,
        )
        with patch("ocms.api.routers.jobs.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.list_all.return_value = cheap_jobs
            mock_repo_cls.return_value.create.return_value = new_job
            mock_repo_cls.return_value.get.return_value = new_job
            resp = client.post(
                "/jobs",
                json={
                    "model_id": "meta-llama/Llama-3.1-8B",
                    "quant_method": "GPTQ",
                    "bits": 4,
                    "instance_type": "g5.xlarge",
                    "region": "us-east-1",
                    "spot": False,
                    "max_runtime_hours": 2,
                },
            )

        assert resp.status_code == 201
