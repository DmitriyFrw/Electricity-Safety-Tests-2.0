"""add user_answers.selected_indexes for multi-select answers

Revision ID: 010_selected_indexes
Revises: 009_correct_indexes
Create Date: 2026-06-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010_selected_indexes"
down_revision: Union[str, None] = "009_correct_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_answers",
        sa.Column("selected_indexes", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_answers", "selected_indexes")
