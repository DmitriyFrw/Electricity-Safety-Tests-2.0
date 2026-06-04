"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-06-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("job_title", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_role", "users", ["role"], unique=False)

    op.create_table(
        "tests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tests_author_id", "tests", ["author_id"], unique=False)

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("test_id", "position", name="uq_ticket_test_position"),
    )
    op.create_index("ix_tickets_test_id", "tickets", ["test_id"], unique=False)

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("correct_index", sa.Integer(), nullable=False),
        sa.Column("option_a", sa.Text(), nullable=False),
        sa.Column("option_b", sa.Text(), nullable=False),
        sa.Column("option_c", sa.Text(), nullable=False),
        sa.Column("option_d", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_questions_ticket_id", "questions", ["ticket_id"], unique=False)

    op.create_table(
        "attempts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attempts_mode", "attempts", ["mode"], unique=False)
    op.create_index("ix_attempts_test_id", "attempts", ["test_id"], unique=False)
    op.create_index("ix_attempts_user_id", "attempts", ["user_id"], unique=False)

    op.create_table(
        "ticket_attempts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timed_out", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "ticket_id", name="uq_attempt_ticket"),
    )
    op.create_index("ix_ticket_attempts_attempt_id", "ticket_attempts", ["attempt_id"], unique=False)
    op.create_index("ix_ticket_attempts_ticket_id", "ticket_attempts", ["ticket_id"], unique=False)

    op.create_table(
        "user_answers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("selected_index", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),
    )
    op.create_index("ix_user_answers_attempt_id", "user_answers", ["attempt_id"], unique=False)
    op.create_index("ix_user_answers_question_id", "user_answers", ["question_id"], unique=False)

    op.create_table(
        "signed_protocols",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("signer_id", sa.Integer(), nullable=False),
        sa.Column("examinee_id", sa.Integer(), nullable=False),
        sa.Column("examinee_full_name", sa.String(length=200), nullable=False),
        sa.Column("examinee_birth_date", sa.Date(), nullable=False),
        sa.Column("examinee_job_title", sa.String(length=200), nullable=False),
        sa.Column("test_title", sa.String(length=200), nullable=False),
        sa.Column("result_percent", sa.Integer(), nullable=False),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"]),
        sa.ForeignKeyConstraint(["examinee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["signer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signed_protocols_attempt_id", "signed_protocols", ["attempt_id"], unique=True)
    op.create_index("ix_signed_protocols_examinee_id", "signed_protocols", ["examinee_id"], unique=False)
    op.create_index("ix_signed_protocols_signer_id", "signed_protocols", ["signer_id"], unique=False)


def downgrade() -> None:
    op.drop_table("signed_protocols")
    op.drop_table("user_answers")
    op.drop_table("ticket_attempts")
    op.drop_table("attempts")
    op.drop_table("questions")
    op.drop_table("tickets")
    op.drop_table("tests")
    op.drop_table("users")
