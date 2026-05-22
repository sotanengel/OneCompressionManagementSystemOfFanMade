"""create jobs and job_logs tables

Revision ID: 0001
Revises:
Create Date: 2026-05-23
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("job_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=True),
        sa.Column("model_id", sa.String(255), nullable=False),
        sa.Column("quant_method", sa.String(50), nullable=False),
        sa.Column("bits", sa.Integer, nullable=False),
        sa.Column("instance_type", sa.String(100), nullable=False),
        sa.Column("region", sa.String(50), nullable=False),
        sa.Column("spot", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("max_runtime_hours", sa.Integer, nullable=False),
        sa.Column("feature_flags", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("ec2_instance_id", sa.String(100), nullable=True),
        sa.Column("s3_output_prefix", sa.String(500), nullable=True),
        sa.Column("estimated_cost_usd", sa.Numeric(10, 4), nullable=True),
        sa.Column("actual_cost_usd", sa.Numeric(10, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text, nullable=True),
        sa.Column("rerun_script_path", sa.String(500), nullable=True),
        sa.Column("git_commit_onecompression", sa.String(40), nullable=True),
        sa.Column("git_commit_sotanengel", sa.String(40), nullable=True),
    )

    op.create_table(
        "job_logs",
        sa.Column("log_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("jobs.job_id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
    )

    op.create_index("ix_job_logs_job_id", "job_logs", ["job_id"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_job_logs_job_id", "job_logs")
    op.drop_index("ix_jobs_status", "jobs")
    op.drop_index("ix_jobs_created_at", "jobs")
    op.drop_table("job_logs")
    op.drop_table("jobs")
