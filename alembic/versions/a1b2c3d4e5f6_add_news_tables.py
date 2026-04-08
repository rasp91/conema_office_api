"""add news tables

Revision ID: a1b2c3d4e5f6
Revises: 880da683bd4b
Create Date: 2026-04-07 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '880da683bd4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'kiosk_news_items',
        sa.Column('id', mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('published_at', sa.Date(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(length=4294967295), nullable=False),
        sa.Column('thumbnail_path', sa.String(500), nullable=True),
        sa.Column('is_visible', sa.Boolean(), nullable=False, server_default='1'),
    )

    op.create_table(
        'kiosk_news_documents',
        sa.Column('id', mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True),
        sa.Column('news_item_id', mysql.BIGINT(unsigned=True), sa.ForeignKey('kiosk_news_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('type', sa.Enum('image', 'file'), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Index('ix_kiosk_news_documents_news_item_id', 'news_item_id'),
    )


def downgrade() -> None:
    op.drop_table('kiosk_news_documents')
    op.drop_table('kiosk_news_items')
