"""add_youtube_to_event_news_internalinfo_docs

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-04-18 22:14:52.537645

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, Sequence[str], None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE kiosk_event_documents MODIFY COLUMN type ENUM('image', 'file', 'youtube') NOT NULL")
    op.execute("ALTER TABLE kiosk_news_documents MODIFY COLUMN type ENUM('image', 'file', 'youtube') NOT NULL")
    op.execute("ALTER TABLE kiosk_internal_info_documents MODIFY COLUMN type ENUM('image', 'file', 'youtube') NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE kiosk_event_documents MODIFY COLUMN type ENUM('image', 'file') NOT NULL")
    op.execute("ALTER TABLE kiosk_news_documents MODIFY COLUMN type ENUM('image', 'file') NOT NULL")
    op.execute("ALTER TABLE kiosk_internal_info_documents MODIFY COLUMN type ENUM('image', 'file') NOT NULL")
