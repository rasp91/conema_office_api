"""add activity_logs table

Revision ID: ed14b4ddee15
Revises: 13d51c3e4b1f
Create Date: 2026-08-07 07:33:08.358161

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ed14b4ddee15"
down_revision: Union[str, Sequence[str], None] = "13d51c3e4b1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "activity_logs",
        sa.Column("id", mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("device_id", sa.String(64), nullable=True),
        sa.Column("device_name", sa.String(100), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("action_type", sa.String(30), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("path", sa.String(255), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Index("ix_activity_logs_created_at", "created_at"),
        sa.Index("ix_activity_logs_resource_type_created_at", "resource_type", "created_at"),
        sa.Index("ix_activity_logs_device_id_created_at", "device_id", "created_at"),
    )


def downgrade() -> None:
    op.drop_table("activity_logs")
