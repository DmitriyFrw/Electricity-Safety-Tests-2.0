"""add tickets.title

Revision ID: 003_ticket_title
Revises: 002_business_unit
Create Date: 2026-06-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_ticket_title"
down_revision: Union[str, None] = "002_business_unit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("title", sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column("tickets", "title")
