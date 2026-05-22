from datetime import UTC

from ocms.core.models import FeatureFlags, Job, JobStatus


def test_job_status_values() -> None:
    assert JobStatus.PENDING == "pending"
    assert JobStatus.EC2_LAUNCHING == "ec2_launching"
    assert JobStatus.RUNNING == "running"
    assert JobStatus.UPLOADING == "uploading"
    assert JobStatus.SYNCING == "syncing"
    assert JobStatus.COMPLETED == "completed"
    assert JobStatus.FAILED == "failed"


def test_job_status_is_str_enum() -> None:
    assert isinstance(JobStatus.PENDING, str)


def test_feature_flags_defaults() -> None:
    flags = FeatureFlags()
    assert flags.check_env_preflight is False
    assert flags.checkpoint is False


def test_feature_flags_can_be_enabled() -> None:
    flags = FeatureFlags(check_env_preflight=True, checkpoint=True)
    assert flags.check_env_preflight is True
    assert flags.checkpoint is True


def test_job_has_required_fields() -> None:
    import uuid
    from datetime import datetime

    job = Job(
        job_id=uuid.uuid4(),
        model_id="meta-llama/Llama-3.1-8B",
        quant_method="GPTQ",
        bits=4,
        instance_type="g5.xlarge",
        region="us-east-1",
        spot=False,
        max_runtime_hours=4,
        status=JobStatus.PENDING,
        feature_flags=FeatureFlags(),
        created_at=datetime.now(UTC),
    )
    assert job.status == JobStatus.PENDING
    assert job.ec2_instance_id is None
    assert job.failure_reason is None
