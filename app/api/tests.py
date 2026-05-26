from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.answer_labels import parse_answer_label
from app.api_serializers import exam_paper_out, exam_result_out, test_edit_out, test_list_out
from app.attempt_service import submit_test_attempt_with_answers
from app.constants import QUESTIONS_PER_TICKET
from app.database import get_db
from app.deps import login_required
from app.models import Question, Test, Ticket, User
from app.schemas import (
    ExamPaperOut,
    ExamResultOut,
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


def _require_owner(db: Session, test_id: int, user: User) -> Test:
    test = db.get(Test, test_id)
    if not test or test.author_id != user.id:
        raise HTTPException(status_code=403, detail="Редактирование доступно только автору")
    return test


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
    user: Annotated[User, Depends(login_required)],
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
    user: Annotated[User, Depends(login_required)],
):
    _require_owner(db, test_id, user)
    test = _load_test_full(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    return test_edit_out(db, test)


@router.get("/{test_id}/exam", response_model=ExamPaperOut)
def get_exam_paper(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    test = _load_test_full(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    if not test_is_ready_to_take(db, test):
        if user.id == test.author_id:
            raise HTTPException(status_code=400, detail="Тест ещё не заполнен полностью")
        raise HTTPException(status_code=400, detail="Тест недоступен для сдачи")
    return exam_paper_out(test)


@router.post("/{test_id}/exam", response_model=ExamResultOut)
def submit_exam(
    test_id: int,
    body: SubmitExamIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    test = _load_test_full(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    if not test_is_ready_to_take(db, test):
        raise HTTPException(status_code=400, detail="Тест недоступен для сдачи")

    answers = {a.question_id: a.value for a in body.answers}
    _attempt, summary, ticket_rows = submit_test_attempt_with_answers(
        db,
        user_id=user.id,
        test=test,
        answers=answers,
    )
    return exam_result_out(test, summary, ticket_rows)


@router.post("/{test_id}/tickets", response_model=TestEditOut, status_code=201)
def add_ticket(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    _require_owner(db, test_id, user)
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
    user: Annotated[User, Depends(login_required)],
):
    _require_owner(db, test_id, user)
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
    user: Annotated[User, Depends(login_required)],
):
    _require_owner(db, test_id, user)
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
