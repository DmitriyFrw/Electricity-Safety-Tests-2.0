"""unique open exam attempt per user and test

Revision ID: 013_open_exam_unique
Revises: 012_wiki_pages
Create Date: 2026-06-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013_open_exam_unique"
down_revision: Union[str, None] = "012_wiki_pages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_INDEX = "uq_open_exam_attempt"
_WHERE = "mode = 'exam' AND finished_at IS NULL"


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            sa.text(
                f"CREATE UNIQUE INDEX {_INDEX} ON attempts (user_id, test_id) WHERE {_WHERE}"
            )
        )
    else:
        op.execute(
            sa.text(
                f"CREATE UNIQUE INDEX IF NOT EXISTS {_INDEX} "
                f"ON attempts (user_id, test_id) WHERE {_WHERE}"
            )
        )


def downgrade() -> None:
    op.drop_index(_INDEX, table_name="attempts")
