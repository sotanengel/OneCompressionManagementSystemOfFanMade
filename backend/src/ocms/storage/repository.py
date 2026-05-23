from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from ocms.core.models import FeatureFlags, Job, JobLog, JobStatus
from ocms.core.state_machine import validate_transition
from ocms.storage.tables import JobLogRow, JobRow


class JobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        model_id: str,
        quant_method: str,
        bits: int,
        instance_type: str,
        region: str,
        spot: bool,
        max_runtime_hours: int,
        feature_flags: FeatureFlags,
        user_id: str | None = None,
        s3_output_prefix: str | None = None,
    ) -> Job:
        row = JobRow(
            job_id=uuid.uuid4(),
            user_id=user_id,
            model_id=model_id,
            quant_method=quant_method,
            bits=bits,
            instance_type=instance_type,
            region=region,
            spot=spot,
            max_runtime_hours=max_runtime_hours,
            feature_flags=asdict(feature_flags),
            status=JobStatus.PENDING,
            s3_output_prefix=s3_output_prefix,
            created_at=datetime.now(UTC),
        )
        self._session.add(row)
        self._session.flush()
        return _to_domain(row)

    def get(self, job_id: uuid.UUID) -> Job | None:
        row = self._session.get(JobRow, job_id)
        return _to_domain(row) if row else None

    def list_all(self) -> list[Job]:
        rows = self._session.query(JobRow).order_by(JobRow.created_at.desc()).all()
        return [_to_domain(r) for r in rows]

    def update_status(
        self,
        job_id: uuid.UUID,
        new_status: JobStatus,
        *,
        ec2_instance_id: str | None = None,
        failure_reason: str | None = None,
        rerun_script_path: str | None = None,
    ) -> Job:
        row = self._session.get(JobRow, job_id)
        if row is None:
            raise ValueError(f"Job {job_id} not found")

        current = JobStatus(row.status)
        validate_transition(current, new_status)

        row.status = new_status
        if ec2_instance_id is not None:
            row.ec2_instance_id = ec2_instance_id
        if failure_reason is not None:
            row.failure_reason = failure_reason
        if rerun_script_path is not None:
            row.rerun_script_path = rerun_script_path
        if new_status == JobStatus.RUNNING and row.started_at is None:
            row.started_at = datetime.now(UTC)
        if new_status in (JobStatus.COMPLETED, JobStatus.FAILED):
            row.completed_at = datetime.now(UTC)

        self._session.flush()
        return _to_domain(row)

    def append_log(
        self,
        *,
        job_id: uuid.UUID,
        level: str,
        source: str,
        message: str,
    ) -> JobLog:
        log_row = JobLogRow(
            log_id=uuid.uuid4(),
            job_id=job_id,
            level=level,
            source=source,
            message=message,
        )
        self._session.add(log_row)
        self._session.flush()
        return _log_to_domain(log_row)

    def get_logs(self, job_id: uuid.UUID) -> list[JobLog]:
        rows = (
            self._session.query(JobLogRow)
            .filter(JobLogRow.job_id == job_id)
            .order_by(JobLogRow.timestamp.asc())
            .all()
        )
        return [_log_to_domain(r) for r in rows]

    def get_logs_since(self, job_id: uuid.UUID, since: datetime | None) -> list[JobLog]:
        self._session.expire_all()
        query = self._session.query(JobLogRow).filter(JobLogRow.job_id == job_id)
        if since is not None:
            query = query.filter(JobLogRow.timestamp > since)
        rows = query.order_by(JobLogRow.timestamp.asc()).all()
        return [_log_to_domain(r) for r in rows]


def _to_domain(row: JobRow) -> Job:
    flags_dict = row.feature_flags or {}
    return Job(
        job_id=row.job_id,
        user_id=row.user_id,
        model_id=row.model_id,
        quant_method=row.quant_method,
        bits=row.bits,
        instance_type=row.instance_type,
        region=row.region,
        spot=row.spot,
        max_runtime_hours=row.max_runtime_hours,
        feature_flags=FeatureFlags(**flags_dict),
        status=JobStatus(row.status),
        ec2_instance_id=row.ec2_instance_id,
        s3_output_prefix=row.s3_output_prefix,
        estimated_cost_usd=Decimal(str(row.estimated_cost_usd)) if row.estimated_cost_usd else None,
        actual_cost_usd=Decimal(str(row.actual_cost_usd)) if row.actual_cost_usd else None,
        created_at=row.created_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
        failure_reason=row.failure_reason,
        rerun_script_path=row.rerun_script_path,
        git_commit_onecompression=row.git_commit_onecompression,
        git_commit_sotanengel=row.git_commit_sotanengel,
    )


def _log_to_domain(row: JobLogRow) -> JobLog:
    return JobLog(
        log_id=row.log_id,
        job_id=row.job_id,
        timestamp=row.timestamp,
        level=row.level,
        source=row.source,
        message=row.message,
    )
