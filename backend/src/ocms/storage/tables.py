from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ocms.storage.db import Base


class JobRow(Base):
    __tablename__ = "jobs"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    quant_method: Mapped[str] = mapped_column(String(50), nullable=False)
    bits: Mapped[int] = mapped_column(Integer, nullable=False)
    instance_type: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    spot: Mapped[bool] = mapped_column(nullable=False, default=False)
    max_runtime_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    feature_flags: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    ec2_instance_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    s3_output_prefix: Mapped[str | None] = mapped_column(String(500), nullable=True)
    estimated_cost_usd: Mapped[float | None] = mapped_column(nullable=True)
    actual_cost_usd: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    rerun_script_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    git_commit_onecompression: Mapped[str | None] = mapped_column(String(40), nullable=True)
    git_commit_sotanengel: Mapped[str | None] = mapped_column(String(40), nullable=True)
    checkpoint_s3_prefix: Mapped[str | None] = mapped_column(Text, nullable=True)
    resumed_from_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.job_id"), nullable=True
    )

    logs: Mapped[list[JobLogRow]] = relationship(
        "JobLogRow", back_populates="job", cascade="all, delete-orphan"
    )


class JobLogRow(Base):
    __tablename__ = "job_logs"

    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.job_id"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    job: Mapped[JobRow] = relationship("JobRow", back_populates="logs")
