from __future__ import annotations

import uuid
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ocms.api.deps import get_db
from ocms.api.schemas import (
    CostEstimateResponse,
    JobCreateRequest,
    JobListResponse,
    JobLogEntryResponse,
    JobLogsResponse,
    JobResponse,
)
from ocms.core.models import FeatureFlags
from ocms.ec2.cost import estimate_cost
from ocms.storage.repository import JobRepository

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _to_response(job) -> JobResponse:  # type: ignore[no-untyped-def]
    return JobResponse(
        job_id=job.job_id,
        user_id=job.user_id,
        model_id=job.model_id,
        quant_method=job.quant_method,
        bits=job.bits,
        instance_type=job.instance_type,
        region=job.region,
        spot=job.spot,
        max_runtime_hours=job.max_runtime_hours,
        status=job.status,
        ec2_instance_id=job.ec2_instance_id,
        s3_output_prefix=job.s3_output_prefix,
        estimated_cost_usd=job.estimated_cost_usd,
        actual_cost_usd=job.actual_cost_usd,
        feature_flags=asdict(job.feature_flags),
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        failure_reason=job.failure_reason,
        rerun_script_path=job.rerun_script_path,
        git_commit_onecompression=job.git_commit_onecompression,
    )


@router.post("", status_code=201, response_model=JobResponse)
def create_job(
    request: JobCreateRequest,
    db: Session = Depends(get_db),
) -> JobResponse:
    repo = JobRepository(db)
    flags = FeatureFlags(
        check_env_preflight=request.feature_flags.check_env_preflight,
        checkpoint=request.feature_flags.checkpoint,
    )
    cost = estimate_cost(
        instance_type=request.instance_type,
        max_runtime_hours=request.max_runtime_hours,
        spot=request.spot,
    )
    job = repo.create(
        model_id=request.model_id,
        quant_method=request.quant_method,
        bits=request.bits,
        instance_type=request.instance_type,
        region=request.region,
        spot=request.spot,
        max_runtime_hours=request.max_runtime_hours,
        feature_flags=flags,
        s3_output_prefix=request.s3_output_prefix,
    )
    # Persist estimated cost via raw update (no status transition needed)
    from ocms.storage.tables import JobRow

    row = db.get(JobRow, job.job_id)
    if row:
        row.estimated_cost_usd = float(cost.estimated_cost_usd)
        db.flush()

    return _to_response(repo.get(job.job_id) or job)


@router.get("", response_model=JobListResponse)
def list_jobs(db: Session = Depends(get_db)) -> JobListResponse:
    repo = JobRepository(db)
    jobs = repo.list_all()
    return JobListResponse(items=[_to_response(j) for j in jobs], total=len(jobs))


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> JobResponse:
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _to_response(job)


@router.get("/{job_id}/logs", response_model=JobLogsResponse)
def get_job_logs(job_id: uuid.UUID, db: Session = Depends(get_db)) -> JobLogsResponse:
    repo = JobRepository(db)
    if not repo.get(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    logs = repo.get_logs(job_id)
    items = [
        JobLogEntryResponse(
            log_id=log.log_id,
            job_id=log.job_id,
            timestamp=log.timestamp,
            level=log.level,
            source=log.source,
            message=log.message,
        )
        for log in logs
    ]
    return JobLogsResponse(items=items, total=len(items))


@router.get("/{job_id}/cost-estimate", response_model=CostEstimateResponse)
def get_cost_estimate(job_id: uuid.UUID, db: Session = Depends(get_db)) -> CostEstimateResponse:
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    cost = estimate_cost(
        instance_type=job.instance_type,
        max_runtime_hours=job.max_runtime_hours,
        spot=job.spot,
    )
    return CostEstimateResponse(
        instance_type=cost.instance_type,
        max_runtime_hours=cost.max_runtime_hours,
        spot=cost.spot,
        estimated_cost_usd=cost.estimated_cost_usd,
        on_demand_rate_usd_hr=cost.on_demand_rate_usd_hr,
        spot_discount_pct=cost.spot_discount_pct,
    )
