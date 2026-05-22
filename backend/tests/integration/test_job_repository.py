import uuid

import pytest

from ocms.core.models import FeatureFlags, JobStatus
from ocms.storage.repository import JobRepository


@pytest.fixture
def repo(db_session):  # type: ignore[no-untyped-def]
    return JobRepository(db_session)


def make_job_kwargs() -> dict:
    return {
        "model_id": "meta-llama/Llama-3.1-8B",
        "quant_method": "GPTQ",
        "bits": 4,
        "instance_type": "g5.xlarge",
        "region": "us-east-1",
        "spot": False,
        "max_runtime_hours": 4,
        "feature_flags": FeatureFlags(),
    }


@pytest.mark.integration
def test_create_and_get_job(repo: JobRepository) -> None:
    job = repo.create(**make_job_kwargs())
    assert job.status == JobStatus.PENDING
    assert job.job_id is not None

    fetched = repo.get(job.job_id)
    assert fetched is not None
    assert fetched.job_id == job.job_id
    assert fetched.model_id == "meta-llama/Llama-3.1-8B"


@pytest.mark.integration
def test_get_nonexistent_returns_none(repo: JobRepository) -> None:
    assert repo.get(uuid.uuid4()) is None


@pytest.mark.integration
def test_list_jobs(repo: JobRepository) -> None:
    repo.create(**make_job_kwargs())
    repo.create(**make_job_kwargs())
    jobs = repo.list_all()
    assert len(jobs) >= 2


@pytest.mark.integration
def test_update_status(repo: JobRepository) -> None:
    job = repo.create(**make_job_kwargs())
    updated = repo.update_status(
        job.job_id,
        JobStatus.EC2_LAUNCHING,
        ec2_instance_id="i-0abc123",
    )
    assert updated.status == JobStatus.EC2_LAUNCHING
    assert updated.ec2_instance_id == "i-0abc123"


@pytest.mark.integration
def test_update_status_invalid_transition_raises(repo: JobRepository) -> None:
    job = repo.create(**make_job_kwargs())
    with pytest.raises(ValueError, match="Invalid transition"):
        repo.update_status(job.job_id, JobStatus.COMPLETED)


@pytest.mark.integration
def test_append_log(repo: JobRepository) -> None:
    job = repo.create(**make_job_kwargs())
    repo.append_log(
        job_id=job.job_id,
        level="INFO",
        source="api",
        message="Job created",
    )
    logs = repo.get_logs(job.job_id)
    assert len(logs) == 1
    assert logs[0].message == "Job created"
    assert logs[0].source == "api"
