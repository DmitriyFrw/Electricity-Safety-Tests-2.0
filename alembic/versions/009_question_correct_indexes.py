"""add questions.correct_indexes for multiple correct answers

Revision ID: 009_correct_indexes
Revises: 008_test_published
Create Date: 2026-06-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_correct_indexes"
down_revision: Union[str, None] = "008_test_published"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("correct_indexes", sa.String(length=32), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE questions SET correct_indexes = CAST(correct_index AS VARCHAR) "
            "WHERE correct_indexes IS NULL"
        )
    )
    op.alter_column("questions", "correct_indexes", nullable=False)


def downgrade() -> None:
    op.drop_column("questions", "correct_indexes")
