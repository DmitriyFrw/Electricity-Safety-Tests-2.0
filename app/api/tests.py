from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import login_required, test_editor_required
from app.exceptions import AppError
from app.form_requests.tests import SubmitExamRequest, TestCreateRequest, TicketSaveRequest
from app.models import User
from app.schemas import (
    ExamPaperOut,
    ExamResultOut,
    ExamSessionOut,
    ExamTicketPaperOut,
    TestCreateOut,
    TestEditOut,
    TestListOut,
)
from app.services.test_service import TestService

router = APIRouter(prefix="/tests", tags=["tests"])


def _handle(fn):
    try:
        return fn()
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.get("", response_model=TestListOut)
def list_tests(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    return TestService.list_tests(db, user)


@router.post("", response_model=TestCreateOut, status_code=201)
def create_test(
    form: TestCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
):
    return _handle(lambda: TestService.create_test(db, user, form))


@router.get("/{test_id}", response_model=TestEditOut)
def get_test_for_edit(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
):
    return _handle(lambda: TestService.get_test_for_edit(db, test_id, user))


@router.get("/{test_id}/training", response_model=ExamPaperOut)
def get_training_paper(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    return _handle(lambda: TestService.get_training_paper(db, test_id, user))


@router.post("/{test_id}/training", response_model=ExamResultOut)
def submit_training(
    test_id: int,
    form: SubmitExamRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    return _handle(lambda: TestService.submit_training(db, test_id, user, form))


@router.post("/{test_id}/exam/session", response_model=ExamSessionOut)
def start_exam_session(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    return _handle(lambda: TestService.start_exam_session(db, test_id, user))


@router.get("/{test_id}/exam/session", response_model=ExamSessionOut)
def get_exam_session(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    return _handle(lambda: TestService.get_exam_session(db, test_id, user))


@router.get("/{test_id}/exam/tickets/{ticket_id}", response_model=ExamTicketPaperOut)
def get_exam_ticket(
    test_id: int,
    ticket_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    return _handle(lambda: TestService.get_exam_ticket(db, test_id, ticket_id, user))


@router.post("/{test_id}/exam/tickets/{ticket_id}", response_model=ExamSessionOut)
def submit_exam_ticket_answers(
    test_id: int,
    ticket_id: int,
    form: SubmitExamRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    return _handle(
        lambda: TestService.submit_exam_ticket_answers(db, test_id, ticket_id, user, form)
    )


@router.post("/{test_id}/exam/finish", response_model=ExamResultOut)
def finish_exam(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
):
    return _handle(lambda: TestService.finish_exam(db, test_id, user))


@router.post("/{test_id}/tickets", response_model=TestEditOut, status_code=201)
def add_ticket(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
):
    return _handle(lambda: TestService.add_ticket(db, test_id, user))


@router.put("/{test_id}/tickets/{ticket_id}", response_model=TestEditOut)
def save_ticket(
    test_id: int,
    ticket_id: int,
    form: TicketSaveRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
):
    return _handle(lambda: TestService.save_ticket(db, test_id, ticket_id, user, form))


@router.delete("/{test_id}/tickets/{ticket_id}", response_model=TestEditOut)
def delete_ticket(
    test_id: int,
    ticket_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
):
    return _handle(lambda: TestService.delete_ticket(db, test_id, ticket_id, user))
