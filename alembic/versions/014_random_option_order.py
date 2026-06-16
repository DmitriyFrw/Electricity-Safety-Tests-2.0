"""add tests.random_option_order and attempts.question_option_orders

Revision ID: 014_random_option_order
Revises: 013_open_exam_unique
Create Date: 2026-06-09

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_random_option_order"
down_revision: Union[str, None] = "013_open_exam_unique"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tests",
        sa.Column("random_option_order", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("tests", "random_option_order", server_default=None)
    op.add_column("attempts", sa.Column("question_option_orders", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("attempts", "question_option_orders")
    op.drop_column("tests", "random_option_order")
