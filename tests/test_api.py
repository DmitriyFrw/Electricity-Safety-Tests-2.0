from __future__ import annotations

import datetime as dt

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.constants import EXAM_TICKET_TIME_LIMIT_SECONDS
from app.auth_utils import hash_password
from app.models import Attempt, Question, Ticket, TicketAttempt, Test, User
from app.database import SessionLocal
from app.main import app


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
    test = Test(author_id=user_id, title="Test 1", description=None, published=True)
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
async def test_admin_can_delete_test_without_attempts(async_client: AsyncClient, db_session):
    admin = User(username="admin_del", password_hash=hash_password("password123"), role="admin")
    db_session.add(admin)
    db_session.commit()

    csrf = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    login = await async_client.post(
        "/api/auth/login",
        json={"username": "admin_del", "password": "password123"},
        headers={"X-CSRF-Token": csrf},
    )
    login.raise_for_status()

    csrf_create = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    created = await async_client.post(
        "/api/tests",
        json={"title": "To Delete", "description": None},
        headers={"X-CSRF-Token": csrf_create},
    )
    created.raise_for_status()
    test_id = created.json()["id"]

    csrf_del = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    deleted = await async_client.delete(
        f"/api/tests/{test_id}",
        headers={"X-CSRF-Token": csrf_del},
    )
    assert deleted.status_code == 204

    missing = await async_client.get(f"/api/tests/{test_id}")
    assert missing.status_code == 404


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
        json={
            "full_name": "Test User",
            "birth_date": "2000-01-01",
            "job_title": "Engineer",
            "business_unit": "ДЦ MOZ",
        },
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

    # Another logged-in user must not access чужую export-задачу.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client2:
        csrf_other = (await client2.get("/api/auth/csrf")).json()["csrf_token"]
        reg_other = await client2.post(
            "/api/auth/register",
            json={"username": "export_u2", "password": "password123", "password2": "password123"},
            headers={"X-CSRF-Token": csrf_other},
        )
        reg_other.raise_for_status()
        forbidden = await client2.get(f"/api/profile/exports/{task_id2}")
        assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_sign_protocol_for_passed_exam(async_client: AsyncClient, db_session):
    # kot user who passes exam
    csrf = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    reg = await async_client.post(
        "/api/auth/register",
        json={"username": "kot_signed", "password": "password123", "password2": "password123"},
        headers={"X-CSRF-Token": csrf},
    )
    reg.raise_for_status()
    kot_user_id = reg.json()["id"]

    s = SessionLocal()
    try:
        kot = s.get(User, kot_user_id)
        assert kot is not None
        kot.full_name = "Кот Тестовый"
        kot.birth_date = dt.date(2000, 1, 1)
        kot.job_title = "Электромонтер"
        kot.business_unit = "ДЦ KLG"
        # add ready test with one ticket
        t = Test(author_id=kot_user_id, title="Signed Exam", description=None, published=True)
        ticket = Ticket(position=1)
        t.tickets.append(ticket)
        for pos in range(1, 11):
            ticket.questions.append(
                Question(
                    position=pos,
                    text=f"Q{pos}",
                    correct_index=0,
                    option_a="A",
                    option_b="B",
                    option_c="C",
                    option_d="D",
                )
            )
        s.add(t)
        s.commit()
        s.refresh(t)
        test_id = t.id
        qids = [q.id for q in ticket.questions]
    finally:
        s.close()

    csrf_sess = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    start = await async_client.post(
        f"/api/tests/{test_id}/exam/session", headers={"X-CSRF-Token": csrf_sess}
    )
    start.raise_for_status()
    sess = start.json()
    ticket_id = sess["next_ticket_id"]
    assert ticket_id is not None
    await async_client.get(f"/api/tests/{test_id}/exam/tickets/{ticket_id}")
    csrf_submit = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    submit = await async_client.post(
        f"/api/tests/{test_id}/exam/tickets/{ticket_id}",
        json={"answers": [{"question_id": qid, "value": "A"} for qid in qids]},
        headers={"X-CSRF-Token": csrf_submit},
    )
    submit.raise_for_status()
    csrf_finish = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    finish = await async_client.post(
        f"/api/tests/{test_id}/exam/finish",
        headers={"X-CSRF-Token": csrf_finish},
    )
    finish.raise_for_status()
    attempt_id = finish.json()["attempt_id"]

    # relogin as admin
    s2 = SessionLocal()
    try:
        admin = User(username="admin_sign", password_hash=hash_password("password123"), role="admin")
        s2.add(admin)
        s2.commit()
    finally:
        s2.close()

    csrf_logout = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    await async_client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf_logout})
    csrf_admin = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    login_admin = await async_client.post(
        "/api/auth/login",
        json={"username": "admin_sign", "password": "password123"},
        headers={"X-CSRF-Token": csrf_admin},
    )
    login_admin.raise_for_status()

    draft_pdf = await async_client.get(
        f"/api/tests/{test_id}/exam/attempts/{attempt_id}/protocol-draft.pdf"
    )
    assert draft_pdf.status_code == 200
    assert draft_pdf.headers.get("content-type", "").startswith("application/pdf")

    form_pdf = await async_client.get(
        f"/api/tests/{test_id}/exam/attempts/{attempt_id}/protocol-form.pdf"
    )
    assert form_pdf.status_code == 200
    assert form_pdf.headers.get("content-type", "").startswith("application/pdf")

    csrf_sign = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    sign = await async_client.post(
        f"/api/tests/{test_id}/exam/attempts/{attempt_id}/protocol/sign",
        headers={"X-CSRF-Token": csrf_sign},
    )
    assert sign.status_code == 200
    assert sign.json()["attempt_id"] == attempt_id
    pdf = await async_client.get(f"/api/tests/{test_id}/exam/attempts/{attempt_id}/protocol.pdf")
    assert pdf.status_code == 200
    assert pdf.headers.get("content-type", "").startswith("application/pdf")

    dash_admin = await async_client.get("/api/dashboard")
    dash_admin.raise_for_status()
    exports = dash_admin.json().get("staff_protocol_exports", [])
    assert len(exports) >= 1
    assert exports[0]["attempt_id"] == attempt_id

    # kot sees signed protocol block data in dashboard
    csrf_logout2 = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    await async_client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf_logout2})
    csrf_kot = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    login_kot = await async_client.post(
        "/api/auth/login",
        json={"username": "kot_signed", "password": "password123"},
        headers={"X-CSRF-Token": csrf_kot},
    )
    login_kot.raise_for_status()
    dash = await async_client.get("/api/dashboard")
    dash.raise_for_status()
    assert dash.json()["signed_protocol"] is not None

    kot_protocol = await async_client.get(
        f"/api/tests/{test_id}/exam/attempts/{attempt_id}/protocol"
    )
    assert kot_protocol.status_code == 200
    kot_pdf = await async_client.get(
        f"/api/tests/{test_id}/exam/attempts/{attempt_id}/protocol.pdf"
    )
    assert kot_pdf.status_code == 200
    assert kot_pdf.headers.get("content-type", "").startswith("application/pdf")

    form_kot = await async_client.get(
        f"/api/tests/{test_id}/exam/attempts/{attempt_id}/protocol-form.pdf"
    )
    assert form_kot.status_code == 403
    draft_kot = await async_client.get(
        f"/api/tests/{test_id}/exam/attempts/{attempt_id}/protocol-draft.pdf"
    )
    assert draft_kot.status_code == 403

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as stranger:
        csrf_stranger = (await stranger.get("/api/auth/csrf")).json()["csrf_token"]
        reg_stranger = await stranger.post(
            "/api/auth/register",
            json={"username": "stranger_proto", "password": "password123", "password2": "password123"},
            headers={"X-CSRF-Token": csrf_stranger},
        )
        reg_stranger.raise_for_status()
        forbidden_meta = await stranger.get(
            f"/api/tests/{test_id}/exam/attempts/{attempt_id}/protocol"
        )
        assert forbidden_meta.status_code == 403
        forbidden_pdf = await stranger.get(
            f"/api/tests/{test_id}/exam/attempts/{attempt_id}/protocol.pdf"
        )
        assert forbidden_pdf.status_code == 403


@pytest.mark.asyncio
async def test_admin_update_user_role(async_client: AsyncClient, db_session):
    kot = User(
        username="kot_role",
        password_hash=hash_password("password123"),
        role="kot",
        full_name="Кот Роль",
        birth_date=dt.date(1990, 5, 5),
        job_title="Инженер",
        business_unit="ДЦ KLG",
    )
    admin = User(username="admin_role", password_hash=hash_password("password123"), role="admin")
    db_session.add_all([kot, admin])
    db_session.commit()

    csrf = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    login = await async_client.post(
        "/api/auth/login",
        json={"username": "admin_role", "password": "password123"},
        headers={"X-CSRF-Token": csrf},
    )
    login.raise_for_status()

    users = await async_client.get("/api/admin/users")
    assert users.status_code == 200
    assert len(users.json()) >= 2
    kot_row = next(u for u in users.json() if u["id"] == kot.id)
    assert kot_row["profile_complete"] is True

    dash_admin = await async_client.get("/api/dashboard")
    dash_admin.raise_for_status()
    drafts = dash_admin.json().get("admin_protocol_drafts", [])
    assert any(d["user_id"] == kot.id for d in drafts)

    draft_pdf = await async_client.get(f"/api/admin/users/{kot.id}/protocol-draft.pdf")
    assert draft_pdf.status_code == 200
    assert draft_pdf.headers.get("content-type", "").startswith("application/pdf")

    csrf2 = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    upd = await async_client.put(
        f"/api/admin/users/{kot.id}/role",
        json={"role": "ezh"},
        headers={"X-CSRF-Token": csrf2},
    )
    assert upd.status_code == 200
    assert upd.json()["role"] == "ezh"

    csrf3 = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    self_upd = await async_client.put(
        f"/api/admin/users/{admin.id}/role",
        json={"role": "kot"},
        headers={"X-CSRF-Token": csrf3},
    )
    assert self_upd.status_code == 400

    await async_client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf3})
    csrf_kot = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    forbidden = await async_client.get("/api/admin/users", headers={"X-CSRF-Token": csrf_kot})
    # kot not logged in for GET without login - need login kot first
    login_kot = await async_client.post(
        "/api/auth/login",
        json={"username": "kot_role", "password": "password123"},
        headers={"X-CSRF-Token": csrf_kot},
    )
    login_kot.raise_for_status()
    forbidden = await async_client.get("/api/admin/users")
    assert forbidden.status_code == 403

    csrf_out = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    await async_client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf_out})
    csrf4 = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    await async_client.post(
        "/api/auth/login",
        json={"username": "admin_role", "password": "password123"},
        headers={"X-CSRF-Token": csrf4},
    )
    csrf5 = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    bad_role = await async_client.put(
        f"/api/admin/users/{kot.id}/role",
        json={"role": "superuser"},
        headers={"X-CSRF-Token": csrf5},
    )
    assert bad_role.status_code == 422


@pytest.mark.asyncio
async def test_exam_session_uses_single_random_ticket(async_client: AsyncClient, db_session):
    user = await async_client.post(
        "/api/auth/register",
        json={"username": "randexam", "password": "password123", "password2": "password123"},
        headers={"X-CSRF-Token": (await async_client.get("/api/auth/csrf")).json()["csrf_token"]},
    )
    user.raise_for_status()
    user_id = user.json()["id"]

    test = Test(author_id=user_id, title="Exam pool", safety_group="II", published=True)
    for pos in range(1, 3):
        ticket = Ticket(position=pos, option_count=4)
        for qpos in range(1, 11):
            ticket.questions.append(
                Question(
                    position=qpos,
                    text=f"Q{pos}-{qpos}",
                    correct_index=0,
                    option_a="A",
                    option_b="B",
                    option_c="C",
                    option_d="D",
                )
            )
        test.tickets.append(ticket)
    db_session.add(test)
    db_session.commit()

    csrf = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    start = await async_client.post(
        f"/api/tests/{test.id}/exam/session",
        headers={"X-CSRF-Token": csrf},
    )
    start.raise_for_status()
    session = start.json()
    assert session["ticket_count"] == 1
    assert session["next_ticket_id"] is not None

    attempt = db_session.get(Attempt, session["attempt_id"])
    assert attempt is not None
    assert attempt.exam_ticket_order is not None
    assert "question_ids" in attempt.exam_ticket_order


@pytest.mark.asyncio
async def test_kot_safety_group_and_exam_assignment(async_client: AsyncClient, db_session):
    csrf = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    kot = await async_client.post(
        "/api/auth/register",
        json={"username": "kot2", "password": "password123", "password2": "password123"},
        headers={"X-CSRF-Token": csrf},
    )
    kot.raise_for_status()
    kot_id = kot.json()["id"]
    assert kot.json()["safety_group"] == "II"

    ezh = User(username="ezh1", password_hash=hash_password("password123"), role="ezh")
    db_session.add(ezh)
    db_session.commit()

    csrf_ezh = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    login_ezh = await async_client.post(
        "/api/auth/login",
        json={"username": "ezh1", "password": "password123"},
        headers={"X-CSRF-Token": csrf_ezh},
    )
    login_ezh.raise_for_status()

    csrf_ezh2 = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    updated = await async_client.put(
        f"/api/staff/kot-users/{kot_id}/safety-group",
        json={"safety_group": "III"},
        headers={"X-CSRF-Token": csrf_ezh2},
    )
    updated.raise_for_status()
    assert updated.json()["safety_group"] == "III"

    test_ii = Test(author_id=ezh.id, title="Exam II", safety_group="II", published=True)
    test_iii = Test(author_id=ezh.id, title="Exam III", safety_group="III", published=True)
    for test_obj, pos_text in ((test_ii, "II"), (test_iii, "III")):
        ticket = Ticket(position=1, option_count=4)
        for pos in range(1, 11):
            ticket.questions.append(
                Question(
                    position=pos,
                    text=f"Q {pos_text}",
                    correct_index=0,
                    option_a="A",
                    option_b="B",
                    option_c="C",
                    option_d="D",
                )
            )
        test_obj.tickets.append(ticket)
    db_session.add_all([test_ii, test_iii])
    db_session.commit()

    csrf_kot = (await async_client.get("/api/auth/csrf")).json()["csrf_token"]
    login_kot = await async_client.post(
        "/api/auth/login",
        json={"username": "kot2", "password": "password123"},
        headers={"X-CSRF-Token": csrf_kot},
    )
    login_kot.raise_for_status()

    dash = await async_client.get("/api/dashboard")
    dash.raise_for_status()
    assert dash.json()["exam_test_id"] == test_iii.id
    assert dash.json()["user"]["safety_group"] == "III"

    listed = await async_client.get("/api/tests")
    listed.raise_for_status()
    ids = {item["id"] for item in listed.json()["items"]}
    assert test_iii.id in ids
    assert test_ii.id not in ids

