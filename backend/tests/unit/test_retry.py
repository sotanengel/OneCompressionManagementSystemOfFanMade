from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from ocms.core.models import FeatureFlags, Job, JobStatus


def _make_job(status: JobStatus = JobStatus.FAILED) -> Job:
    return Job(
        job_id=uuid.uuid4(),
        user_id=None,
        model_id="Qwen/Qwen3-1.7B",
        quant_method="GPTQ",
        bits=4,
        instance_type="g5.xlarge",
        region="us-east-1",
        spot=True,
        max_runtime_hours=4,
        feature_flags=FeatureFlags(checkpoint=True),
        status=status,
        ec2_instance_id=None,
        s3_output_prefix="s3://ocms-bucket/jobs/abc/output/",
        estimated_cost_usd=Decimal("1.00"),
        actual_cost_usd=None,
        created_at=datetime.now(UTC),
        started_at=None,
        completed_at=None,
        failure_reason="spot_interrupted",
        rerun_script_path=None,
        git_commit_onecompression=None,
        git_commit_sotanengel=None,
    )


@pytest.fixture
def client() -> TestClient:
    from fastapi import FastAPI

    from ocms.api.auth import verify_cognito_jwt
    from ocms.api.deps import get_db
    from ocms.api.routers.jobs import router

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[verify_cognito_jwt] = lambda: "test-user"
    return TestClient(app, raise_server_exceptions=False)


class TestRetryEndpoint:
    @patch("ocms.api.routers.jobs.JobRepository")
    def test_retry_returns_404_for_unknown_job(
        self, mock_repo_cls: MagicMock, client: TestClient
    ) -> None:
        mock_repo_cls.return_value.get.return_value = None
        resp = client.post(f"/jobs/{uuid.uuid4()}/retry")
        assert resp.status_code == 404

    @mock_aws
    @patch("ocms.api.routers.jobs.JobRepository")
    def test_retry_without_checkpoint_creates_new_job(
        self, mock_repo_cls: MagicMock, client: TestClient
    ) -> None:
        original_job = _make_job()
        new_job = _make_job(status=JobStatus.PENDING)
        mock_repo = mock_repo_cls.return_value
        mock_repo.get.return_value = original_job
        mock_repo.create.return_value = new_job

        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="ocms-bucket")

        resp = client.post(f"/jobs/{original_job.job_id}/retry")
        assert resp.status_code == 201
        mock_repo.create.assert_called_once()

    @mock_aws
    @patch("ocms.api.routers.jobs.JobRepository")
    def test_retry_with_checkpoint_passes_resume_flag(
        self, mock_repo_cls: MagicMock, client: TestClient
    ) -> None:
        original_job = _make_job()
        new_job = _make_job(status=JobStatus.PENDING)
        mock_repo = mock_repo_cls.return_value
        mock_repo.get.return_value = original_job
        mock_repo.create.return_value = new_job

        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="ocms-bucket")
        s3.put_object(
            Bucket="ocms-bucket",
            Key=f"jobs/{original_job.job_id}/checkpoint/latest/config.json",
            Body=b"{}",
        )

        resp = client.post(f"/jobs/{original_job.job_id}/retry")
        assert resp.status_code == 201
        call_kwargs = mock_repo.create.call_args.kwargs
        assert call_kwargs.get("checkpoint_s3_prefix") is not None

    @patch("ocms.api.routers.jobs.JobRepository")
    def test_retry_only_failed_or_cancelled_jobs(
        self, mock_repo_cls: MagicMock, client: TestClient
    ) -> None:
        running_job = _make_job(status=JobStatus.RUNNING)
        mock_repo_cls.return_value.get.return_value = running_job
        resp = client.post(f"/jobs/{running_job.job_id}/retry")
        assert resp.status_code == 409

    @patch("ocms.api.routers.jobs.boto3.client")
    @patch("ocms.api.routers.jobs.JobRepository")
    def test_retry_502_when_bucket_missing(
        self,
        mock_repo_cls: MagicMock,
        mock_boto: MagicMock,
        client: TestClient,
    ) -> None:
        from botocore.exceptions import ClientError

        original_job = _make_job()
        mock_repo_cls.return_value.get.return_value = original_job

        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "not found"}},
            "ListObjectsV2",
        )
        mock_boto.return_value = mock_s3

        resp = client.post(f"/jobs/{original_job.job_id}/retry")
        assert resp.status_code == 502
        mock_repo_cls.return_value.create.assert_not_called()

    @patch("ocms.api.routers.jobs.boto3.client")
    @patch("ocms.api.routers.jobs.JobRepository")
    def test_retry_502_when_access_denied(
        self,
        mock_repo_cls: MagicMock,
        mock_boto: MagicMock,
        client: TestClient,
    ) -> None:
        from botocore.exceptions import ClientError

        original_job = _make_job()
        mock_repo_cls.return_value.get.return_value = original_job

        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}},
            "ListObjectsV2",
        )
        mock_boto.return_value = mock_s3

        resp = client.post(f"/jobs/{original_job.job_id}/retry")
        assert resp.status_code == 502
        mock_repo_cls.return_value.create.assert_not_called()

    @patch("ocms.api.routers.jobs.boto3.client")
    @patch("ocms.api.routers.jobs.JobRepository")
    def test_retry_continues_on_non_fatal_s3_error(
        self,
        mock_repo_cls: MagicMock,
        mock_boto: MagicMock,
        client: TestClient,
    ) -> None:
        from botocore.exceptions import ClientError

        original_job = _make_job()
        new_job = _make_job(status=JobStatus.PENDING)
        mock_repo_cls.return_value.get.return_value = original_job
        mock_repo_cls.return_value.create.return_value = new_job

        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.side_effect = ClientError(
            {"Error": {"Code": "SlowDown", "Message": "throttled"}},
            "ListObjectsV2",
        )
        mock_boto.return_value = mock_s3

        resp = client.post(f"/jobs/{original_job.job_id}/retry")
        assert resp.status_code == 201
        kwargs = mock_repo_cls.return_value.create.call_args.kwargs
        assert kwargs.get("checkpoint_s3_prefix") is None
