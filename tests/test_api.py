from __future__ import annotations

import datetime as dt

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.constants import EXAM_TICKET_TIME_LIMIT_SECONDS
from app.auth_utils import hash_password
from app.models import Question, Ticket, TicketAttempt, Test, User
from app.database import SessionLocal


@pytest.mark.asyncio
async def test_health_has_correlation_id(async_client: AsyncClient):
    r = await async_client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    assert "X-Correlation-ID" in r.headers


@pytest.mark.asyncio
async def test_csrf_required(async_client: AsyncClient):
    r = await async_client.post(
        "/api/auth/register",
        json={"username": "u1", "password": "password123", "password2": "password123"},
    )
    assert r.status_code == 403
    body = r.json()
    assert "detail" in body
    assert "CSRF" in body["detail"] or "токен" in body["detail"] or isinstance(body["detail"], str)
    assert "X-Correlation-ID" in r.headers


@pytest.mark.asyncio
async def test_exam_ticket_timeout(async_client: AsyncClient, db_session):
    # 1) Auth session
    user = await async_client.post(
        "/api/auth/register",
        json={"username": "examuser", "password": "password123", "password2": "password123"},
        headers={"X-CSRF-Token": (await async_client.get("/api/auth/csrf")).json()["csrf_token"]},
    )
    user.raise_for_status()
    user_id = user.json()["id"]

    # 2) Create ready test in DB for this user
    test = Test(author_id=user_id, title="Test 1", description=None)
    ticket = Ticket(position=1)
    test.tickets.append(ticket)

    for pos in range(1, 11):
        # correct_index: 0..3
        q = Question(
            position=pos,
            text=f"Question {pos}",
            correct_index=(pos - 1) % 4,
            option_a="A1",
            option_b="B1",
            option_c="C1",
            option_d="D1",
        )
        ticket.questions.append(q)

    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)

    # 3) Start exam session
    csrf = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    start = await async_client.post(
        f"/api/tests/{test.id}/exam/session", headers={"X-CSRF-Token": csrf}
    )
    start.raise_for_status()
    session = start.json()
    next_ticket_id = session["next_ticket_id"]
    assert next_ticket_id is not None

    # 4) Open the ticket (creates TicketAttempt)
    await async_client.get(f"/api/tests/{test.id}/exam/tickets/{next_ticket_id}")

    # 5) Force ticket attempt to be expired
    now = dt.datetime.now(dt.timezone.utc)
    expired_started_at = now - dt.timedelta(seconds=EXAM_TICKET_TIME_LIMIT_SECONDS + 5)

    s2 = SessionLocal()
    try:
        ta = s2.execute(
            select(TicketAttempt).where(
                TicketAttempt.attempt_id == session["attempt_id"],
                TicketAttempt.ticket_id == next_ticket_id,
            )
        ).scalar_one()
        ta.started_at = expired_started_at
        s2.commit()
    finally:
        s2.close()

    # 6) Submit ticket answers -> should timeout
    csrf2 = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    submit = await async_client.post(
        f"/api/tests/{test.id}/exam/tickets/{next_ticket_id}",
        json={"answers": [{"question_id": q.id, "value": "A"} for q in ticket.questions]},
        headers={"X-CSRF-Token": csrf2},
    )
    assert submit.status_code == 408
    assert "X-Correlation-ID" in submit.headers

