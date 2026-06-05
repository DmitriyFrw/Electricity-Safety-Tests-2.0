"""add users.business_unit

Revision ID: 002_business_unit
Revises: 001_initial
Create Date: 2026-06-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_business_unit"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("business_unit", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "business_unit")
