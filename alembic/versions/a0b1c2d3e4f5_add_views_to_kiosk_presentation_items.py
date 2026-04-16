"""add views to kiosk presentation items

Revision ID: a0b1c2d3e4f5
Revises: f3a4b5c6d7e8
Create Date: 2026-04-14 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a0b1c2d3e4f5"
down_revision: Union[str, Sequence[str], None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("kiosk_presentation_items", sa.Column("views", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("kiosk_presentation_items", "views")
