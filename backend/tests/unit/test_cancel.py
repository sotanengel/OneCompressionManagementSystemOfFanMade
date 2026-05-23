from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ocms.api.deps import get_db
from ocms.core.models import FeatureFlags, Job, JobStatus
from ocms.main import app


def _make_job(
    status: JobStatus = JobStatus.PENDING,
    ec2_instance_id: str | None = None,
    region: str = "us-east-1",
) -> Job:
    return Job(
        job_id=uuid.uuid4(),
        model_id="meta-llama/Llama-3.1-8B",
        quant_method="GPTQ",
        bits=4,
        instance_type="g5.xlarge",
        region=region,
        spot=False,
        max_runtime_hours=2,
        status=status,
        feature_flags=FeatureFlags(),
        created_at=datetime.now(UTC),
        ec2_instance_id=ec2_instance_id,
    )


@pytest.fixture()
def client():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestCancelJob:
    def test_cancel_pending_job_returns_204(self, client: TestClient) -> None:
        job = _make_job(status=JobStatus.PENDING)
        with patch("ocms.api.routers.cancel.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.get.return_value = job
            mock_repo_cls.return_value.update_status.return_value = job
            resp = client.post(f"/jobs/{job.job_id}/cancel")

        assert resp.status_code == 204

    def test_cancel_running_job_returns_204(self, client: TestClient) -> None:
        job = _make_job(status=JobStatus.RUNNING, ec2_instance_id="i-12345678")
        with patch("ocms.api.routers.cancel.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.get.return_value = job
            mock_repo_cls.return_value.update_status.return_value = job
            with patch("ocms.api.routers.cancel.boto3") as mock_boto3:
                mock_boto3.client.return_value.terminate_instances.return_value = {}
                resp = client.post(f"/jobs/{job.job_id}/cancel")

        assert resp.status_code == 204

    def test_cancel_running_job_terminates_ec2(self, client: TestClient) -> None:
        job = _make_job(status=JobStatus.RUNNING, ec2_instance_id="i-abcdef01")
        with patch("ocms.api.routers.cancel.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.get.return_value = job
            mock_repo_cls.return_value.update_status.return_value = job
            with patch("ocms.api.routers.cancel.boto3") as mock_boto3:
                ec2_client = MagicMock()
                mock_boto3.client.return_value = ec2_client
                client.post(f"/jobs/{job.job_id}/cancel")

        ec2_client.terminate_instances.assert_called_once_with(InstanceIds=["i-abcdef01"])

    def test_cancel_completed_job_returns_409(self, client: TestClient) -> None:
        job = _make_job(status=JobStatus.COMPLETED)
        with patch("ocms.api.routers.cancel.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.get.return_value = job
            resp = client.post(f"/jobs/{job.job_id}/cancel")

        assert resp.status_code == 409

    def test_cancel_nonexistent_job_returns_404(self, client: TestClient) -> None:
        with patch("ocms.api.routers.cancel.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.get.return_value = None
            resp = client.post(f"/jobs/{uuid.uuid4()}/cancel")

        assert resp.status_code == 404

    def test_cancel_updates_status_to_cancelled(self, client: TestClient) -> None:
        job = _make_job(status=JobStatus.PENDING)
        with patch("ocms.api.routers.cancel.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.get.return_value = job
            mock_repo_cls.return_value.update_status.return_value = job
            client.post(f"/jobs/{job.job_id}/cancel")

        mock_repo_cls.return_value.update_status.assert_called_once_with(
            job.job_id, JobStatus.CANCELLED
        )

    def test_cancel_ec2_launching_job_terminates_ec2(self, client: TestClient) -> None:
        job = _make_job(status=JobStatus.EC2_LAUNCHING, ec2_instance_id="i-launching")
        with patch("ocms.api.routers.cancel.JobRepository") as mock_repo_cls:
            mock_repo_cls.return_value.get.return_value = job
            mock_repo_cls.return_value.update_status.return_value = job
            with patch("ocms.api.routers.cancel.boto3") as mock_boto3:
                ec2_client = MagicMock()
                mock_boto3.client.return_value = ec2_client
                resp = client.post(f"/jobs/{job.job_id}/cancel")

        assert resp.status_code == 204
        ec2_client.terminate_instances.assert_called_once_with(InstanceIds=["i-launching"])
