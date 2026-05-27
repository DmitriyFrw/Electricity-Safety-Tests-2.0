from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.answer_labels import parse_answer_label
from app.api_serializers import (
    exam_paper_out,
    exam_result_out,
    exam_session_out,
    exam_ticket_paper_out,
    test_edit_out,
    test_list_out,
)
from app.attempt_service import submit_test_attempt_with_answers
from app.constants import QUESTIONS_PER_TICKET
from app.database import get_db
from app.deps import login_required, require_test_edit_access, test_editor_required
from app.exam_service import (
    completed_ticket_ids,
    create_exam_attempt,
    finish_exam_attempt,
    get_open_exam_attempt,
    next_ticket,
    start_ticket_for_exam,
    submit_exam_ticket,
    ticket_deadline,
)
from app.models import Question, Test, Ticket, User
from app.schemas import (
    ExamPaperOut,
    ExamResultOut,
    ExamSessionOut,
    ExamTicketPaperOut,
    MessageOut,
    SubmitExamIn,
    TestCreateIn,
    TestCreateOut,
    TestEditOut,
    TestListOut,
    TicketSaveIn,
)
from app.validation import assert_can_add_ticket, test_is_ready_to_take

router = APIRouter(prefix="/tests", tags=["tests"])


def _load_test_full(db: Session, test_id: int) -> Test | None:
    return (
        db.query(Test)
        .options(selectinload(Test.tickets).selectinload(Ticket.questions))
        .filter(Test.id == test_id)
        .one_or_none()
    )


def _require_ready_test(db: Session, test: Test, user: User) -> None:
    if not test_is_ready_to_take(db, test):
        if user.id == test.author_id:
            raise HTTPException(status_code=400, detail="Тест ещё не заполнен полностью")
        raise HTTPException(status_code=400, detail="Тест недоступен для сдачи")


@router.get("", response_model=TestListOut)
def list_tests(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    tests = (
        db.query(Test)
        .options(selectinload(Test.author), selectinload(Test.tickets))
        .order_by(Test.created_at.desc())
        .all()
    )
    return test_list_out(db, tests, user)


@router.post("", response_model=TestCreateOut, status_code=201)
def create_test(
    body: TestCreateIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
):
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Укажите название")
    test = Test(
        author_id=user.id,
        title=title,
        description=(body.description or "").strip() or None,
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    return TestCreateOut(id=test.id, title=test.title)


@router.get("/{test_id}", response_model=TestEditOut)
def get_test_for_edit(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
):
    require_test_edit_access(db, test_id, user)
    test = _load_test_full(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    return test_edit_out(db, test)


@router.get("/{test_id}/training", response_model=ExamPaperOut)
def get_training_paper(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    test = _load_test_full(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    _require_ready_test(db, test, user)
    return exam_paper_out(test)


@router.post("/{test_id}/training", response_model=ExamResultOut)
def submit_training(
    test_id: int,
    body: SubmitExamIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    test = _load_test_full(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    _require_ready_test(db, test, user)
    answers = {a.question_id: a.value for a in body.answers}
    _attempt, summary, ticket_rows = submit_test_attempt_with_answers(
        db,
        user_id=user.id,
        test=test,
        answers=answers,
    )
    return exam_result_out(test, summary, ticket_rows)


@router.post("/{test_id}/exam/session", response_model=ExamSessionOut)
def start_exam_session(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    test = _load_test_full(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    _require_ready_test(db, test, user)
    attempt = create_exam_attempt(db, user_id=user.id, test_id=test.id)
    done = set(completed_ticket_ids(db, attempt))
    nxt = next_ticket(test, done)
    return exam_session_out(
        attempt_id=attempt.id,
        test=test,
        completed_ticket_ids=sorted(done),
        next_ticket_id=nxt.id if nxt else None,
    )


@router.get("/{test_id}/exam/session", response_model=ExamSessionOut)
def get_exam_session(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    test = _load_test_full(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    attempt = get_open_exam_attempt(db, user_id=user.id, test_id=test_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Нет активной экзаменационной сессии")
    done = set(completed_ticket_ids(db, attempt))
    nxt = next_ticket(test, done)
    return exam_session_out(
        attempt_id=attempt.id,
        test=test,
        completed_ticket_ids=sorted(done),
        next_ticket_id=nxt.id if nxt else None,
    )


@router.get("/{test_id}/exam/tickets/{ticket_id}", response_model=ExamTicketPaperOut)
def get_exam_ticket(
    test_id: int,
    ticket_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    test = _load_test_full(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    _require_ready_test(db, test, user)
    attempt = get_open_exam_attempt(db, user_id=user.id, test_id=test_id)
    if not attempt:
        raise HTTPException(status_code=400, detail="Сначала начните экзамен")
    ticket = db.get(Ticket, ticket_id)
    if not ticket or ticket.test_id != test_id:
        raise HTTPException(status_code=404, detail="Билет не найден")
    tickets_sorted = sorted(test.tickets, key=lambda t: t.position)
    try:
        ta, remaining = start_ticket_for_exam(db, attempt=attempt, ticket=ticket, test=test)
    except ValueError as e:
        raise HTTPException(status_code=408, detail=str(e)) from e
    ticket_index = next(i for i, t in enumerate(tickets_sorted, start=1) if t.id == ticket.id)
    return exam_ticket_paper_out(
        test=test,
        attempt_id=attempt.id,
        ticket=ticket,
        ticket_index=ticket_index,
        seconds_remaining=remaining,
        deadline_at=ticket_deadline(ta.started_at),
    )


@router.post("/{test_id}/exam/tickets/{ticket_id}", response_model=ExamSessionOut)
def submit_exam_ticket_answers(
    test_id: int,
    ticket_id: int,
    body: SubmitExamIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    test = _load_test_full(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    attempt = get_open_exam_attempt(db, user_id=user.id, test_id=test_id)
    if not attempt:
        raise HTTPException(status_code=400, detail="Нет активной экзаменационной сессии")
    ticket = db.get(Ticket, ticket_id)
    if not ticket or ticket.test_id != test_id:
        raise HTTPException(status_code=404, detail="Билет не найден")
    answers = {a.question_id: a.value for a in body.answers}
    try:
        submit_exam_ticket(db, attempt=attempt, ticket=ticket, answers=answers)
    except ValueError as e:
        raise HTTPException(status_code=408, detail=str(e)) from e
    done = set(completed_ticket_ids(db, attempt))
    nxt = next_ticket(test, done)
    return exam_session_out(
        attempt_id=attempt.id,
        test=test,
        completed_ticket_ids=sorted(done),
        next_ticket_id=nxt.id if nxt else None,
    )


@router.post("/{test_id}/exam/finish", response_model=ExamResultOut)
def finish_exam(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    test = _load_test_full(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    attempt = get_open_exam_attempt(db, user_id=user.id, test_id=test_id)
    if not attempt:
        raise HTTPException(status_code=400, detail="Нет активной экзаменационной сессии")
    try:
        summary, ticket_rows = finish_exam_attempt(db, attempt=attempt, test=test)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return exam_result_out(test, summary, ticket_rows)


@router.post("/{test_id}/tickets", response_model=TestEditOut, status_code=201)
def add_ticket(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
):
    require_test_edit_access(db, test_id, user)
    try:
        assert_can_add_ticket(db, test_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
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
    test = _load_test_full(db, test_id)
    return test_edit_out(db, test)  # type: ignore[arg-type]


@router.put("/{test_id}/tickets/{ticket_id}", response_model=TestEditOut)
def save_ticket(
    test_id: int,
    ticket_id: int,
    body: TicketSaveIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
):
    require_test_edit_access(db, test_id, user)
    ticket = db.get(Ticket, ticket_id)
    if not ticket or ticket.test_id != test_id:
        raise HTTPException(status_code=404, detail="Билет не найден")
    if len(body.questions) != QUESTIONS_PER_TICKET:
        raise HTTPException(
            status_code=400,
            detail=f"Нужно ровно {QUESTIONS_PER_TICKET} вопросов",
        )
    for qin in body.questions:
        q = (
            db.query(Question)
            .filter(Question.ticket_id == ticket_id, Question.position == qin.position)
            .one_or_none()
        )
        if not q:
            continue
        ci = parse_answer_label(qin.correct)
        q.text = qin.text.strip()
        q.option_a = qin.option_a.strip()
        q.option_b = qin.option_b.strip()
        q.option_c = qin.option_c.strip()
        q.option_d = qin.option_d.strip()
        q.correct_index = ci if ci is not None else 0
    db.commit()
    test = _load_test_full(db, test_id)
    return test_edit_out(db, test)  # type: ignore[arg-type]


@router.delete("/{test_id}/tickets/{ticket_id}", response_model=TestEditOut)
def delete_ticket(
    test_id: int,
    ticket_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
):
    require_test_edit_access(db, test_id, user)
    ticket = db.get(Ticket, ticket_id)
    if not ticket or ticket.test_id != test_id:
        raise HTTPException(status_code=404, detail="Билет не найден")
    db.delete(ticket)
    db.flush()
    remaining = (
        db.query(Ticket).filter(Ticket.test_id == test_id).order_by(Ticket.position).all()
    )
    for i, t in enumerate(remaining, start=1):
        t.position = i
    db.commit()
    test = _load_test_full(db, test_id)
    return test_edit_out(db, test)  # type: ignore[arg-type]
