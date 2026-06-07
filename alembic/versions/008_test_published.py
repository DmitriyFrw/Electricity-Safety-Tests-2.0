"""add tests.published flag

Revision ID: 008_test_published
Revises: 007_safety_i_ii_iii
Create Date: 2026-06-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import Session, selectinload

revision: str = "008_test_published"
down_revision: Union[str, None] = "007_safety_i_ii_iii"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tests",
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("tests", "published", server_default=None)

    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        from app.models import Question, Test, Ticket
        from app.support.validation import test_is_ready_to_take

        tests = (
            session.query(Test)
            .options(selectinload(Test.tickets).selectinload(Ticket.questions))
            .all()
        )
        for test in tests:
            if test_is_ready_to_take(session, test):
                test.published = True
        session.commit()
    finally:
        session.close()


def downgrade() -> None:
    op.drop_column("tests", "published")
