"""add youtube type to kiosk presentation documents

Revision ID: b8c9d0e1f2a3
Revises: f3a4b5c6d7e8
Create Date: 2026-04-18 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "a4b5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE kiosk_presentation_documents MODIFY COLUMN type ENUM('image', 'file', 'youtube') NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE kiosk_presentation_documents MODIFY COLUMN type ENUM('image', 'file') NOT NULL")
