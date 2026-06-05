"""add tickets.option_count

Revision ID: 004_option_count
Revises: 003_ticket_title
Create Date: 2026-06-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_option_count"
down_revision: Union[str, None] = "003_ticket_title"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tickets",
        sa.Column("option_count", sa.Integer(), nullable=False, server_default="4"),
    )
    op.alter_column("tickets", "option_count", server_default=None)


def downgrade() -> None:
    op.drop_column("tickets", "option_count")
