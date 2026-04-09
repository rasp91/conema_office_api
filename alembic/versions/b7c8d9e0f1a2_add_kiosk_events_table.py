"""add kiosk events table

Revision ID: b7c8d9e0f1a2
Revises: c478178f2f27
Create Date: 2026-04-09 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = '21a21190b227'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'kiosk_events',
        sa.Column('id', mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('time', sa.String(5), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(length=4294967295), nullable=False),
        sa.Column('thumbnail_path', sa.String(500), nullable=True),
        sa.Column('is_visible', sa.Boolean(), nullable=False, server_default='1'),
    )


def downgrade() -> None:
    op.drop_table('kiosk_events')
