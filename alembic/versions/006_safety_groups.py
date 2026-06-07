"""add safety_group to users and tests

Revision ID: 006_safety_groups
Revises: 005_random_order
Create Date: 2026-06-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_safety_groups"
down_revision: Union[str, None] = "005_random_order"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("safety_group", sa.String(length=8), nullable=True))
    op.create_index("ix_users_safety_group", "users", ["safety_group"], unique=False)
    op.execute("UPDATE users SET safety_group = 'II' WHERE role = 'kot' AND safety_group IS NULL")

    op.add_column(
        "tests",
        sa.Column("safety_group", sa.String(length=8), nullable=False, server_default="II"),
    )
    op.create_index("ix_tests_safety_group", "tests", ["safety_group"], unique=False)
    op.alter_column("tests", "safety_group", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_tests_safety_group", table_name="tests")
    op.drop_column("tests", "safety_group")
    op.drop_index("ix_users_safety_group", table_name="users")
    op.drop_column("users", "safety_group")
