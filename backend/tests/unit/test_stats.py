from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from ocms.api.routers.stats import compute_job_stats
from ocms.core.models import FeatureFlags, Job, JobStatus


def _job(
    *,
    status: JobStatus,
    created_offset_hours: float = 0,
    completed_offset_hours: float | None = None,
    duration_sec: float | None = None,
    method: str = "GPTQ",
    failure_reason: str | None = None,
) -> Job:
    now = datetime.now(UTC)
    created = now - timedelta(hours=created_offset_hours)
    completed = None
    started = None
    if completed_offset_hours is not None:
        completed = now - timedelta(hours=completed_offset_hours)
        if duration_sec is not None:
            started = completed - timedelta(seconds=duration_sec)
    return Job(
        job_id=uuid.uuid4(),
        model_id="meta-llama/Llama-3.1-8B",
        quant_method=method,
        bits=4,
        instance_type="g5.xlarge",
        region="us-east-1",
        spot=False,
        max_runtime_hours=2,
        status=status,
        feature_flags=FeatureFlags(),
        created_at=created,
        started_at=started,
        completed_at=completed,
        failure_reason=failure_reason,
    )


def test_empty_jobs_returns_zero_counts() -> None:
    result = compute_job_stats([], period="week")
    assert result.total_jobs == 0
    assert result.status_counts[JobStatus.PENDING.value] == 0
    assert result.status_counts[JobStatus.COMPLETED.value] == 0
    assert result.queue_depth.pending == 0
    assert result.throughput == []
    assert result.failure_reasons == []


def test_status_counts_include_every_status() -> None:
    jobs = [
        _job(status=JobStatus.PENDING),
        _job(status=JobStatus.PENDING),
        _job(status=JobStatus.RUNNING),
        _job(status=JobStatus.COMPLETED, completed_offset_hours=1),
        _job(status=JobStatus.FAILED, failure_reason="spot_interrupted"),
    ]
    result = compute_job_stats(jobs, period="week")
    assert result.total_jobs == 5
    assert result.status_counts[JobStatus.PENDING.value] == 2
    assert result.status_counts[JobStatus.RUNNING.value] == 1
    assert result.status_counts[JobStatus.COMPLETED.value] == 1
    assert result.status_counts[JobStatus.FAILED.value] == 1
    # statuses with zero count are still present
    assert result.status_counts[JobStatus.UPLOADING.value] == 0


def test_queue_depth_only_counts_active_states() -> None:
    jobs = [
        _job(status=JobStatus.PENDING),
        _job(status=JobStatus.EC2_LAUNCHING),
        _job(status=JobStatus.RUNNING),
        _job(status=JobStatus.COMPLETED, completed_offset_hours=1),
    ]
    result = compute_job_stats(jobs, period="week")
    assert result.queue_depth.pending == 1
    assert result.queue_depth.ec2_launching == 1
    assert result.queue_depth.running == 1


def test_throughput_buckets_by_completion_day() -> None:
    jobs = [
        _job(status=JobStatus.COMPLETED, completed_offset_hours=1),
        _job(status=JobStatus.COMPLETED, completed_offset_hours=2),
        _job(status=JobStatus.COMPLETED, completed_offset_hours=25),
        _job(status=JobStatus.RUNNING),  # not completed, ignored
    ]
    result = compute_job_stats(jobs, period="week")
    counts = {p.date: p.count for p in result.throughput}
    assert sum(counts.values()) == 3
    assert len(counts) in (1, 2)  # depending on UTC day boundary


def test_period_filter_drops_old_jobs() -> None:
    jobs = [
        _job(status=JobStatus.COMPLETED, created_offset_hours=10),
        _job(status=JobStatus.COMPLETED, created_offset_hours=24 * 40),  # >30 days
    ]
    week = compute_job_stats(jobs, period="week")
    month = compute_job_stats(jobs, period="month")
    all_time = compute_job_stats(jobs, period="all")
    assert week.total_jobs == 1
    assert month.total_jobs == 1
    assert all_time.total_jobs == 2


def test_avg_duration_grouped_by_method() -> None:
    jobs = [
        _job(
            status=JobStatus.COMPLETED,
            completed_offset_hours=1,
            duration_sec=100,
            method="GPTQ",
        ),
        _job(
            status=JobStatus.COMPLETED,
            completed_offset_hours=1,
            duration_sec=300,
            method="GPTQ",
        ),
        _job(
            status=JobStatus.COMPLETED,
            completed_offset_hours=1,
            duration_sec=600,
            method="AWQ",
        ),
    ]
    result = compute_job_stats(jobs, period="week")
    assert result.avg_duration_sec_by_method["GPTQ"] == 200
    assert result.avg_duration_sec_by_method["AWQ"] == 600


def test_failure_reasons_ranked_and_capped() -> None:
    reasons = ["spot_interrupted"] * 5 + ["oom"] * 3 + ["disk_full"] * 2
    jobs = [_job(status=JobStatus.FAILED, failure_reason=r) for r in reasons]
    # plus a failure with no reason (excluded)
    jobs.append(_job(status=JobStatus.FAILED))
    result = compute_job_stats(jobs, period="week")
    assert [fr.reason for fr in result.failure_reasons] == [
        "spot_interrupted",
        "oom",
        "disk_full",
    ]
    assert [fr.count for fr in result.failure_reasons] == [5, 3, 2]
