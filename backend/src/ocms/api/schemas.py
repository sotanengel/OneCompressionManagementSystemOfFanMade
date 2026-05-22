from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class QuantMethod(StrEnum):
    GPTQ = "GPTQ"
    AWQ = "AWQ"
    SMOOTH_QUANT = "SmoothQuant"
    FP8 = "FP8"


class JobStatus(StrEnum):
    PENDING = "pending"
    EC2_LAUNCHING = "ec2_launching"
    RUNNING = "running"
    UPLOADING = "uploading"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"


class FeatureFlagsRequest(BaseModel):
    check_env_preflight: bool = False
    checkpoint: bool = False


class JobCreateRequest(BaseModel):
    model_id: str
    quant_method: QuantMethod
    bits: int = Field(..., ge=4, le=8)
    instance_type: str = Field(..., examples=["g5.xlarge", "g6e.xlarge"])
    region: str = "us-east-1"
    spot: bool = False
    max_runtime_hours: int = Field(default=4, ge=1, le=48)
    feature_flags: FeatureFlagsRequest = Field(default_factory=FeatureFlagsRequest)
    s3_output_prefix: str | None = None

    @model_validator(mode="after")
    def validate_fp8_bits(self) -> JobCreateRequest:
        if self.quant_method == QuantMethod.FP8 and self.bits != 8:
            raise ValueError("FP8 quantization requires bits=8")
        return self


class JobResponse(BaseModel):
    job_id: uuid.UUID
    user_id: str | None
    model_id: str
    quant_method: str
    bits: int
    instance_type: str
    region: str
    spot: bool
    max_runtime_hours: int
    status: str
    ec2_instance_id: str | None
    s3_output_prefix: str | None
    estimated_cost_usd: Decimal | None
    actual_cost_usd: Decimal | None
    feature_flags: dict[str, Any]
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    failure_reason: str | None
    rerun_script_path: str | None
    git_commit_onecompression: str | None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int


class JobLogEntryResponse(BaseModel):
    log_id: uuid.UUID
    job_id: uuid.UUID
    timestamp: datetime
    level: str
    source: str
    message: str

    model_config = {"from_attributes": True}


class JobLogsResponse(BaseModel):
    items: list[JobLogEntryResponse]
    total: int


class CostEstimateResponse(BaseModel):
    instance_type: str
    max_runtime_hours: int
    spot: bool
    estimated_cost_usd: Decimal
    on_demand_rate_usd_hr: Decimal
    spot_discount_pct: float | None
