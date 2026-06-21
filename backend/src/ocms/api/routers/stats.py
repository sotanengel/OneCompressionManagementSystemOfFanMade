from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ocms.api.auth import verify_cognito_jwt
from ocms.api.deps import get_db
from ocms.api.schemas import (
    FailureReason,
    JobStatsResponse,
    QueueDepth,
    ThroughputPoint,
)
from ocms.core.models import Job, JobStatus
from ocms.storage.repository import JobRepository

router = APIRouter(
    prefix="/stats",
    tags=["stats"],
    dependencies=[Depends(verify_cognito_jwt)],
)

_PERIOD_DAYS: dict[str, int | None] = {
    "week": 7,
    "month": 30,
    "all": None,
}


def _filter_by_period(jobs: list[Job], period: str) -> list[Job]:
    days = _PERIOD_DAYS.get(period)
    if days is None:
        return jobs
    cutoff = datetime.now(UTC) - timedelta(days=days)
    return [j for j in jobs if j.created_at >= cutoff]


def compute_job_stats(jobs: list[Job], *, period: str = "week") -> JobStatsResponse:
    filtered = _filter_by_period(jobs, period)

    status_counts: dict[str, int] = {s.value: 0 for s in JobStatus}
    for job in filtered:
        status_counts[job.status.value] += 1

    queue = QueueDepth(
        pending=status_counts[JobStatus.PENDING.value],
        ec2_launching=status_counts[JobStatus.EC2_LAUNCHING.value],
        running=status_counts[JobStatus.RUNNING.value],
    )

    daily: Counter[str] = Counter()
    for job in filtered:
        if job.status is JobStatus.COMPLETED and job.completed_at is not None:
            daily[job.completed_at.date().isoformat()] += 1
    throughput = [
        ThroughputPoint(date=d, count=c) for d, c in sorted(daily.items())
    ]

    durations: dict[str, list[float]] = defaultdict(list)
    for job in filtered:
        if (
            job.status is JobStatus.COMPLETED
            and job.started_at is not None
            and job.completed_at is not None
        ):
            seconds = (job.completed_at - job.started_at).total_seconds()
            if seconds > 0:
                durations[job.quant_method].append(seconds)
    avg_duration = {
        method: sum(values) / len(values) for method, values in durations.items()
    }

    reason_counts: Counter[str] = Counter()
    for job in filtered:
        if job.status is JobStatus.FAILED and job.failure_reason:
            reason_counts[job.failure_reason] += 1
    failure_reasons = [
        FailureReason(reason=r, count=c) for r, c in reason_counts.most_common(10)
    ]

    return JobStatsResponse(
        period=period,
        total_jobs=len(filtered),
        status_counts=status_counts,
        queue_depth=queue,
        throughput=throughput,
        avg_duration_sec_by_method=avg_duration,
        failure_reasons=failure_reasons,
    )


@router.get("/jobs", response_model=JobStatsResponse)
def get_job_stats(
    period: str = "week",
    db: Session = Depends(get_db),
) -> JobStatsResponse:
    repo = JobRepository(db)
    return compute_job_stats(repo.list_all(), period=period)
