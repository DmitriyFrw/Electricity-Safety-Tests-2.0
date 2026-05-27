from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc)
    )

    tests_created: Mapped[list[Test]] = relationship(
        "Test", back_populates="author", foreign_keys="Test.author_id"
    )
    attempts: Mapped[list[Attempt]] = relationship("Attempt", back_populates="user")


class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc)
    )

    author: Mapped[User] = relationship("User", back_populates="tests_created", foreign_keys=[author_id])
    tickets: Mapped[list[Ticket]] = relationship(
        "Ticket", back_populates="test", order_by="Ticket.position", cascade="all, delete-orphan"
    )
    attempts: Mapped[list[Attempt]] = relationship("Attempt", back_populates="test")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    test: Mapped[Test] = relationship("Test", back_populates="tickets")
    questions: Mapped[list[Question]] = relationship(
        "Question",
        back_populates="ticket",
        order_by="Question.position",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("test_id", "position", name="uq_ticket_test_position"),)


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..10 (см. app.constants.QUESTIONS_PER_TICKET)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # correct: 0=A/1, 1=B/2, 2=C/3, 3=D/4
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)
    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)

    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="questions")
    answers: Mapped[list[UserAnswer]] = relationship("UserAnswer", back_populates="question")


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="training", index=True)
    started_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc)
    )
    finished_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="attempts")
    test: Mapped[Test] = relationship("Test", back_populates="attempts")
    user_answers: Mapped[list[UserAnswer]] = relationship(
        "UserAnswer", back_populates="attempt", cascade="all, delete-orphan"
    )
    ticket_attempts: Mapped[list["TicketAttempt"]] = relationship(
        "TicketAttempt", back_populates="attempt", cascade="all, delete-orphan"
    )


class TicketAttempt(Base):
    __tablename__ = "ticket_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id"), nullable=False, index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False, index=True)
    started_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc)
    )
    finished_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    timed_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    attempt: Mapped[Attempt] = relationship("Attempt", back_populates="ticket_attempts")
    ticket: Mapped[Ticket] = relationship("Ticket")

    __table_args__ = (UniqueConstraint("attempt_id", "ticket_id", name="uq_attempt_ticket"),)


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id"), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False, index=True)
    selected_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0..3, NULL = нет ответа

    attempt: Mapped[Attempt] = relationship("Attempt", back_populates="user_answers")
    question: Mapped[Question] = relationship("Question", back_populates="answers")

    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),)
