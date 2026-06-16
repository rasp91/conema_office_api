"""add server_default to possibilist_documents sort_order

Revision ID: cf3207ea1b89
Revises: b44cde4010a5
Create Date: 2026-06-15 23:16:58.974001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf3207ea1b89'
down_revision: Union[str, Sequence[str], None] = 'b44cde4010a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "kiosk_possibilist_documents",
        "sort_order",
        existing_type=sa.Integer(),
        nullable=False,
        server_default="0",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "kiosk_possibilist_documents",
        "sort_order",
        existing_type=sa.Integer(),
        nullable=False,
        server_default=None,
    )
