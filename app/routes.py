from __future__ import annotations

from typing import Annotated, Any, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, selectinload

from app.answer_labels import INDEX_TO_DIGIT, INDEX_TO_LETTER, parse_answer_label
from app.attempt_service import attempt_to_row, submit_test_attempt
from app.auth_utils import hash_password, verify_password
from app.constants import MAX_TICKETS_PER_TEST, MIN_PASS_PERCENT, QUESTIONS_PER_TICKET
from app.support.grading import exam_is_passed
from app.dashboard_stats import build_dashboard_context
from app.database import get_db
from app.deps import get_current_user_optional, login_required
from app.models import Attempt, Question, Test, Ticket, User, UserAnswer
from app.validation import (
    assert_can_add_ticket,
    test_is_ready_to_take,
    ticket_is_complete,
)
from app.web import templates

router = APIRouter()


def _dashboard_context(
    db: Session,
    user: User,
    nav: str,
    *,
    request: Request,
    **extra: Any,
) -> dict[str, Any]:
    ctx = build_dashboard_context(db, user)
    ctx["nav"] = nav
    ctx["user"] = user
    ctx["request"] = request
    ctx.update(extra)
    return ctx


def _load_tests_catalog(db: Session) -> tuple[list[Test], dict[int, bool]]:
    tests = (
        db.query(Test)
        .options(selectinload(Test.author), selectinload(Test.tickets))
        .order_by(Test.created_at.desc())
        .all()
    )
    ready_flags = {t.id: test_is_ready_to_take(db, t) for t in tests}
    return tests, ready_flags


def _require_author_test(db: Session, test_id: int, user: User) -> Test | None:
    test = db.get(Test, test_id)
    if not test or test.author_id != user.id:
        return None
    return test


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse("/cabinet", status_code=302)
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def register_get(request: Request, db: Annotated[Session, Depends(get_db)]):
    if get_current_user_optional(request, db):
        return RedirectResponse("/cabinet", status_code=302)
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.post("/register", response_class=HTMLResponse)
def register_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    password2: Annotated[str, Form()],
):
    err: Optional[str] = None
    u = username.strip()
    if len(u) < 3:
        err = "Логин не короче 3 символов."
    elif len(password) < 6:
        err = "Пароль не короче 6 символов."
    elif password != password2:
        err = "Пароли не совпадают."
    elif db.query(User).filter(User.username == u).first():
        err = "Такой логин уже занят."
    if err:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": err},
            status_code=400,
        )
    user = User(username=u, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    request.session["user_id"] = user.id
    return RedirectResponse("/cabinet", status_code=302)


@router.get("/login", response_class=HTMLResponse)
def login_get(request: Request, db: Annotated[Session, Depends(get_db)]):
    if get_current_user_optional(request, db):
        return RedirectResponse("/cabinet", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
def login_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    u = username.strip()
    user = db.query(User).filter(User.username == u).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный логин или пароль."},
            status_code=400,
        )
    request.session["user_id"] = user.id
    return RedirectResponse("/cabinet", status_code=302)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)


@router.get("/cabinet", response_class=HTMLResponse)
def cabinet(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    created = (
        db.query(Test)
        .options(selectinload(Test.tickets))
        .filter(Test.author_id == user.id)
        .order_by(Test.created_at.desc())
        .all()
    )
    attempts = (
        db.query(Attempt)
        .options(selectinload(Attempt.test), selectinload(Attempt.user_answers))
        .filter(Attempt.user_id == user.id, Attempt.finished_at.isnot(None))
        .order_by(Attempt.finished_at.desc())
        .limit(100)
        .all()
    )
    attempt_rows = [attempt_to_row(db, a) for a in attempts]
    ctx = _dashboard_context(
        db,
        user,
        "home",
        request=request,
        created_tests=created,
        attempt_rows=attempt_rows,
    )
    return templates.TemplateResponse("cabinet.html", ctx)


@router.get("/training", response_class=HTMLResponse)
def training(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    tests, ready_flags = _load_tests_catalog(db)
    ctx = _dashboard_context(
        db,
        user,
        "training",
        request=request,
        tests=tests,
        ready_flags=ready_flags,
    )
    return templates.TemplateResponse("training.html", ctx)


@router.get("/tests/catalog", response_class=HTMLResponse)
def tests_catalog(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    tests, ready_flags = _load_tests_catalog(db)
    ctx = _dashboard_context(
        db,
        user,
        "exam",
        request=request,
        tests=tests,
        ready_flags=ready_flags,
    )
    return templates.TemplateResponse("catalog.html", ctx)


@router.get("/tests/new", response_class=HTMLResponse)
def test_new_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    ctx = _dashboard_context(db, user, "home", request=request, error=None)
    return templates.TemplateResponse("test_new.html", ctx)


@router.post("/tests/new", response_class=HTMLResponse)
def test_new_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
    title: Annotated[str, Form()],
    description: Annotated[Optional[str], Form()] = None,
):
    t = title.strip()
    if not t:
        ctx = _dashboard_context(
            db,
            user,
            "home",
            request=request,
            error="Укажите название.",
        )
        return templates.TemplateResponse("test_new.html", ctx, status_code=400)
    test = Test(author_id=user.id, title=t, description=(description or "").strip() or None)
    db.add(test)
    db.commit()
    db.refresh(test)
    return RedirectResponse(f"/tests/{test.id}/edit", status_code=302)


@router.get("/tests/{test_id}/edit", response_class=HTMLResponse)
def test_edit_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
    test_id: int,
):
    if not _require_author_test(db, test_id, user):
        return RedirectResponse("/tests/catalog", status_code=302)
    test = (
        db.query(Test)
        .options(selectinload(Test.tickets).selectinload(Ticket.questions))
        .filter(Test.id == test_id)
        .one()
    )
    tickets = sorted(test.tickets, key=lambda x: x.position)
    ctx = _dashboard_context(
        db,
        user,
        "home",
        request=request,
        test=test,
        tickets=tickets,
        max_tickets=MAX_TICKETS_PER_TEST,
        questions_per_ticket=QUESTIONS_PER_TICKET,
        ticket_is_complete=ticket_is_complete,
        ready=test_is_ready_to_take(db, test),
        error=request.query_params.get("err"),
    )
    return templates.TemplateResponse("test_edit.html", ctx)


@router.post("/tests/{test_id}/ticket/add", response_class=HTMLResponse)
def ticket_add(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
    test_id: int,
):
    if not _require_author_test(db, test_id, user):
        return RedirectResponse("/tests/catalog", status_code=302)
    try:
        assert_can_add_ticket(db, test_id)
    except ValueError as e:
        return RedirectResponse(
            f"/tests/{test_id}/edit?err={quote(str(e))}",
            status_code=302,
        )
    pos = db.query(Ticket).filter(Ticket.test_id == test_id).count() + 1
    ticket = Ticket(test_id=test_id, position=pos)
    db.add(ticket)
    db.flush()
    for p in range(1, QUESTIONS_PER_TICKET + 1):
        db.add(
            Question(
                ticket_id=ticket.id,
                position=p,
                text="",
                correct_index=0,
                option_a="",
                option_b="",
                option_c="",
                option_d="",
            )
        )
    db.commit()
    return RedirectResponse(f"/tests/{test_id}/edit", status_code=302)


@router.post("/tests/{test_id}/ticket/{ticket_id}/save", response_class=HTMLResponse)
async def ticket_save(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
    test_id: int,
    ticket_id: int,
):
    test = db.get(Test, test_id)
    ticket = db.get(Ticket, ticket_id)
    if not test or not ticket or ticket.test_id != test_id:
        return RedirectResponse("/tests/catalog", status_code=302)
    if test.author_id != user.id:
        return RedirectResponse("/tests/catalog", status_code=302)

    form = await request.form()
    for pos in range(1, QUESTIONS_PER_TICKET + 1):
        q = (
            db.query(Question)
            .filter(Question.ticket_id == ticket_id, Question.position == pos)
            .one_or_none()
        )
        if not q:
            continue
        ci = parse_answer_label(str(form.get(f"q{pos}_correct") or ""))
        q.text = str(form.get(f"q{pos}_text") or "").strip()
        q.option_a = str(form.get(f"q{pos}_a") or "").strip()
        q.option_b = str(form.get(f"q{pos}_b") or "").strip()
        q.option_c = str(form.get(f"q{pos}_c") or "").strip()
        q.option_d = str(form.get(f"q{pos}_d") or "").strip()
        q.correct_index = ci if ci is not None else 0
    db.commit()
    return RedirectResponse(f"/tests/{test_id}/edit", status_code=302)


@router.post("/tests/{test_id}/ticket/{ticket_id}/delete", response_class=HTMLResponse)
def ticket_delete(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
    test_id: int,
    ticket_id: int,
):
    test = db.get(Test, test_id)
    ticket = db.get(Ticket, ticket_id)
    if not test or not ticket or ticket.test_id != test_id:
        return RedirectResponse("/tests/catalog", status_code=302)
    if test.author_id != user.id:
        return RedirectResponse("/tests/catalog", status_code=302)
    db.delete(ticket)
    db.flush()
    remaining = (
        db.query(Ticket).filter(Ticket.test_id == test_id).order_by(Ticket.position).all()
    )
    for i, t in enumerate(remaining, start=1):
        t.position = i
    db.commit()
    return RedirectResponse(f"/tests/{test_id}/edit", status_code=302)


def _load_test_for_take(db: Session, test_id: int) -> Test | None:
    return (
        db.query(Test)
        .options(selectinload(Test.tickets).selectinload(Ticket.questions))
        .filter(Test.id == test_id)
        .one_or_none()
    )


@router.get("/tests/{test_id}/take", response_class=HTMLResponse)
def take_test_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
    test_id: int,
):
    test = _load_test_for_take(db, test_id)
    if not test:
        return RedirectResponse("/tests/catalog", status_code=302)
    if not test_is_ready_to_take(db, test):
        if user.id == test.author_id:
            return RedirectResponse(f"/tests/{test_id}/edit", status_code=302)
        return RedirectResponse("/tests/catalog", status_code=302)
    ctx = _dashboard_context(
        db,
        user,
        "exam",
        request=request,
        test=test,
        tickets=sorted(test.tickets, key=lambda t: t.position),
        letters=INDEX_TO_LETTER,
        digits=INDEX_TO_DIGIT,
    )
    return templates.TemplateResponse("take_test.html", ctx)


@router.post("/tests/{test_id}/take", response_class=HTMLResponse)
async def take_test_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
    test_id: int,
):
    test = _load_test_for_take(db, test_id)
    if not test:
        return RedirectResponse("/tests/catalog", status_code=302)
    if not test_is_ready_to_take(db, test):
        if user.id == test.author_id:
            return RedirectResponse(f"/tests/{test_id}/edit", status_code=302)
        return RedirectResponse("/tests/catalog", status_code=302)

    form = await request.form()
    _attempt, summary, ticket_rows = submit_test_attempt(
        db, user_id=user.id, test=test, form=form
    )

    ctx = _dashboard_context(
        db,
        user,
        "exam",
        request=request,
        test=test,
        correct=summary.correct,
        total=summary.total,
        percent=summary.percent,
        grade=summary.grade,
        grade_class=summary.grade_class,
        ticket_rows=ticket_rows,
        last_errors=summary.errors,
        passed_exam=exam_is_passed(summary.percent),
    )
    return templates.TemplateResponse("take_result.html", ctx)
