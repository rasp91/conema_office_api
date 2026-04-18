from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "a4b5c6d7e8f9"
down_revision: Union[str, Sequence[str], None] = "a0b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kiosk_internal_info_items",
        sa.Column("id", mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.Column("published_at", sa.Date(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(length=4294967295), nullable=False),
        sa.Column("thumbnail_path", sa.String(500), nullable=True),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "kiosk_internal_info_documents",
        sa.Column("id", mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True),
        sa.Column(
            "info_item_id",
            mysql.BIGINT(unsigned=True),
            sa.ForeignKey("kiosk_internal_info_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("type", sa.Enum("image", "file"), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Index("ix_kiosk_internal_info_documents_info_item_id", "info_item_id"),
    )


def downgrade() -> None:
    op.drop_table("kiosk_internal_info_documents")
    op.drop_table("kiosk_internal_info_items")
