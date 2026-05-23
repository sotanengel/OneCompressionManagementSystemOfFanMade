from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class JobStatus(StrEnum):
    PENDING = "pending"
    EC2_LAUNCHING = "ec2_launching"
    RUNNING = "running"
    UPLOADING = "uploading"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class FeatureFlags:
    check_env_preflight: bool = False
    checkpoint: bool = False


@dataclass
class Job:
    job_id: uuid.UUID
    model_id: str
    quant_method: str
    bits: int
    instance_type: str
    region: str
    spot: bool
    max_runtime_hours: int
    status: JobStatus
    feature_flags: FeatureFlags
    created_at: datetime
    user_id: str | None = None
    ec2_instance_id: str | None = None
    s3_output_prefix: str | None = None
    estimated_cost_usd: Decimal | None = None
    actual_cost_usd: Decimal | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failure_reason: str | None = None
    rerun_script_path: str | None = None
    git_commit_onecompression: str | None = None
    git_commit_sotanengel: str | None = None
    checkpoint_s3_prefix: str | None = None
    resumed_from_job_id: uuid.UUID | None = None
    priority: int = 0


@dataclass
class JobLog:
    log_id: uuid.UUID
    job_id: uuid.UUID
    timestamp: datetime
    level: str
    source: str
    message: str
