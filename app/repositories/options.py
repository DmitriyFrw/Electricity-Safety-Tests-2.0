from __future__ import annotations

from sqlalchemy.orm import selectinload

from app.models import Attempt, SignedProtocol, Test, Ticket

TEST_WITH_TICKETS = selectinload(Test.tickets).selectinload(Ticket.questions)
TEST_WITH_AUTHOR = selectinload(Test.author)
TEST_LIST_OPTIONS = (TEST_WITH_AUTHOR, selectinload(Test.tickets))
TEST_FULL_OPTIONS = (TEST_WITH_AUTHOR, TEST_WITH_TICKETS)

ATTEMPT_DASHBOARD_OPTIONS = (
    selectinload(Attempt.test),
    selectinload(Attempt.user_answers),
)

ATTEMPT_STAFF_PROTOCOL_OPTIONS = (
    *ATTEMPT_DASHBOARD_OPTIONS,
    selectinload(Attempt.user),
)

SIGNED_PROTOCOL_OPTIONS = (
    selectinload(SignedProtocol.attempt),
    selectinload(SignedProtocol.signer),
    selectinload(SignedProtocol.examinee),
)
