"""add checkpoint fields to jobs

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-23
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("checkpoint_s3_prefix", sa.Text, nullable=True))
    op.add_column(
        "jobs",
        sa.Column(
            "resumed_from_job_id",
            UUID(as_uuid=True),
            sa.ForeignKey("jobs.job_id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("jobs", "resumed_from_job_id")
    op.drop_column("jobs", "checkpoint_s3_prefix")
