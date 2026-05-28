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


@pytest.mark.asyncio
async def test_kot_cannot_create_test(async_client: AsyncClient):
    csrf = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    reg = await async_client.post(
        "/api/auth/register",
        json={"username": "kotuser", "password": "password123", "password2": "password123"},
        headers={"X-CSRF-Token": csrf},
    )
    reg.raise_for_status()
    assert reg.json()["role"] == "kot"

    csrf2 = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    create = await async_client.post(
        "/api/tests",
        json={"title": "Forbidden", "description": None},
        headers={"X-CSRF-Token": csrf2},
    )
    assert create.status_code == 403


@pytest.mark.asyncio
async def test_login_rate_limit_bruteforce(async_client: AsyncClient):
    csrf = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    reg = await async_client.post(
        "/api/auth/register",
        json={"username": "ratelimit_u", "password": "password123", "password2": "password123"},
        headers={"X-CSRF-Token": csrf},
    )
    reg.raise_for_status()

    for _ in range(5):
        csrf_login = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
        bad = await async_client.post(
            "/api/auth/login",
            json={"username": "ratelimit_u", "password": "wrong-pass"},
            headers={"X-CSRF-Token": csrf_login},
        )
        assert bad.status_code == 400

    csrf_blocked = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    blocked = await async_client.post(
        "/api/auth/login",
        json={"username": "ratelimit_u", "password": "wrong-pass"},
        headers={"X-CSRF-Token": csrf_blocked},
    )
    assert blocked.status_code == 429


@pytest.mark.asyncio
async def test_async_profile_exports(async_client: AsyncClient):
    csrf = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    reg = await async_client.post(
        "/api/auth/register",
        json={"username": "export_u", "password": "password123", "password2": "password123"},
        headers={"X-CSRF-Token": csrf},
    )
    reg.raise_for_status()

    csrf_upd = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    upd = await async_client.put(
        "/api/profile",
        json={"full_name": "Test User", "birth_date": "2000-01-01", "job_title": "Engineer"},
        headers={"X-CSRF-Token": csrf_upd},
    )
    upd.raise_for_status()

    csrf_exp = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    task_res = await async_client.post("/api/profile/protocol.pdf/export", headers={"X-CSRF-Token": csrf_exp})
    assert task_res.status_code == 202
    task_id = task_res.json()["task_id"]

    done_pdf = None
    for _ in range(50):
        r = await async_client.get(f"/api/profile/exports/{task_id}")
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("application/pdf"):
            done_pdf = r
            break
    assert done_pdf is not None

    csrf_exp2 = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    task_res2 = await async_client.post("/api/profile/attempts/export", headers={"X-CSRF-Token": csrf_exp2})
    assert task_res2.status_code == 202
    task_id2 = task_res2.json()["task_id"]

    done_csv = None
    for _ in range(50):
        r = await async_client.get(f"/api/profile/exports/{task_id2}")
        if r.status_code == 200 and "text/csv" in r.headers.get("content-type", ""):
            done_csv = r
            break
    assert done_csv is not None

