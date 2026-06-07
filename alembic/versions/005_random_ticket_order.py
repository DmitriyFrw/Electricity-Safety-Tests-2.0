"""add tests.random_ticket_order and attempts.exam_ticket_order

Revision ID: 005_random_order
Revises: 004_option_count
Create Date: 2026-06-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_random_order"
down_revision: Union[str, None] = "004_option_count"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tests",
        sa.Column("random_ticket_order", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("tests", "random_ticket_order", server_default=None)
    op.add_column("attempts", sa.Column("exam_ticket_order", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("attempts", "exam_ticket_order")
    op.drop_column("tests", "random_ticket_order")
