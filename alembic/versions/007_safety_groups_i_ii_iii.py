"""remap safety groups to I, II, III

Revision ID: 007_safety_i_ii_iii
Revises: 006_safety_groups
Create Date: 2026-06-05

"""

from typing import Sequence, Union

from alembic import op

revision: str = "007_safety_i_ii_iii"
down_revision: Union[str, None] = "006_safety_groups"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE users SET safety_group = 'III' WHERE safety_group = 'IV'")
    op.execute("UPDATE tests SET safety_group = 'III' WHERE safety_group = 'IV'")


def downgrade() -> None:
    op.execute("UPDATE users SET safety_group = 'IV' WHERE safety_group = 'III'")
    op.execute("UPDATE tests SET safety_group = 'IV' WHERE safety_group = 'III'")
