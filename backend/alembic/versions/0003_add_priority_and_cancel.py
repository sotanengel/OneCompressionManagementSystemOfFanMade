"""add priority column to jobs

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-23
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("jobs", "priority")
