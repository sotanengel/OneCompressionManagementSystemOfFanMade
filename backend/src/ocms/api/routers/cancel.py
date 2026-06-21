from __future__ import annotations

import contextlib
import uuid

import boto3
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ocms.api.auth import verify_cognito_jwt
from ocms.api.deps import get_db
from ocms.core.models import JobStatus
from ocms.storage.repository import JobRepository

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(verify_cognito_jwt)],
)

_CANCELLABLE_STATUSES = {JobStatus.PENDING, JobStatus.EC2_LAUNCHING, JobStatus.RUNNING}
_EC2_STATUSES = {JobStatus.EC2_LAUNCHING, JobStatus.RUNNING}


@router.post("/{job_id}/cancel", status_code=204)
def cancel_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Response:
    repo = JobRepository(db)
    job = repo.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in _CANCELLABLE_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel job in status '{job.status}'",
        )

    if job.ec2_instance_id and job.status in _EC2_STATUSES:
        ec2 = boto3.client("ec2", region_name=job.region)
        with contextlib.suppress(Exception):
            ec2.terminate_instances(InstanceIds=[job.ec2_instance_id])

    repo.update_status(job_id, JobStatus.CANCELLED)
    return Response(status_code=204)
