from __future__ import annotations

from ocms.core.models import JobStatus

ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.PENDING: {JobStatus.EC2_LAUNCHING, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.EC2_LAUNCHING: {JobStatus.RUNNING, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.RUNNING: {JobStatus.UPLOADING, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.UPLOADING: {JobStatus.SYNCING, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.SYNCING: {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.COMPLETED: set(),
    JobStatus.FAILED: set(),
    JobStatus.CANCELLED: set(),
}


def validate_transition(from_status: JobStatus, to_status: JobStatus) -> None:
    allowed = ALLOWED_TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        raise ValueError(
            f"Invalid transition: {from_status!r} → {to_status!r}. "
            f"Allowed: {sorted(s.value for s in allowed)}"
        )
