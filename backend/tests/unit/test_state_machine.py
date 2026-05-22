import pytest

from ocms.core.models import JobStatus
from ocms.core.state_machine import validate_transition

VALID_TRANSITIONS = [
    (JobStatus.PENDING, JobStatus.EC2_LAUNCHING),
    (JobStatus.EC2_LAUNCHING, JobStatus.RUNNING),
    (JobStatus.RUNNING, JobStatus.UPLOADING),
    (JobStatus.UPLOADING, JobStatus.SYNCING),
    (JobStatus.SYNCING, JobStatus.COMPLETED),
    # Any state can transition to FAILED
    (JobStatus.PENDING, JobStatus.FAILED),
    (JobStatus.EC2_LAUNCHING, JobStatus.FAILED),
    (JobStatus.RUNNING, JobStatus.FAILED),
    (JobStatus.UPLOADING, JobStatus.FAILED),
    (JobStatus.SYNCING, JobStatus.FAILED),
]

INVALID_TRANSITIONS = [
    (JobStatus.PENDING, JobStatus.RUNNING),
    (JobStatus.PENDING, JobStatus.COMPLETED),
    (JobStatus.RUNNING, JobStatus.PENDING),
    (JobStatus.COMPLETED, JobStatus.PENDING),
    (JobStatus.FAILED, JobStatus.RUNNING),
    (JobStatus.COMPLETED, JobStatus.FAILED),
]


@pytest.mark.parametrize("from_status,to_status", VALID_TRANSITIONS)
def test_valid_transition(from_status: JobStatus, to_status: JobStatus) -> None:
    validate_transition(from_status, to_status)  # should not raise


@pytest.mark.parametrize("from_status,to_status", INVALID_TRANSITIONS)
def test_invalid_transition_raises(from_status: JobStatus, to_status: JobStatus) -> None:
    with pytest.raises(ValueError, match="Invalid transition"):
        validate_transition(from_status, to_status)
