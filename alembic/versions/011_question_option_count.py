"""add questions.option_count per question

Revision ID: 011_question_option_count
Revises: 010_selected_indexes
Create Date: 2026-06-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011_question_option_count"
down_revision: Union[str, None] = "010_selected_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("option_count", sa.Integer(), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE questions AS q SET option_count = t.option_count "
            "FROM tickets AS t WHERE q.ticket_id = t.id AND q.option_count IS NULL"
        )
    )
    op.execute(sa.text("UPDATE questions SET option_count = 4 WHERE option_count IS NULL"))
    op.alter_column("questions", "option_count", nullable=False)


def downgrade() -> None:
    op.drop_column("questions", "option_count")
