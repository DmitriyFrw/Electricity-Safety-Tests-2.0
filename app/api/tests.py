from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import login_required, test_editor_required
from app.cqrs.bus import dispatch_command, dispatch_query
from app.cqrs.deps import get_command_bus
from app.cqrs.messages import (
    AddTicketCommand,
    CreateTestCommand,
    DeleteTestCommand,
    DeleteTicketCommand,
    FinishExamCommand,
    GetExamAttemptResultQuery,
    GetExamSessionQuery,
    GetAttemptProtocolDraftPdfQuery,
    GetAttemptProtocolFormPdfQuery,
    GetSignedProtocolPdfQuery,
    GetSignedProtocolQuery,
    GetTestForEditQuery,
    GetTrainingPaperQuery,
    ListTestsQuery,
    OpenExamTicketCommand,
    SaveTicketCommand,
    SignProtocolCommand,
    PublishTestCommand,
    UpdateTestSettingsCommand,
    StartExamSessionCommand,
    SubmitExamTicketAnswersCommand,
    SubmitTrainingCommand,
)
from app.database import get_db
from app.form_requests.tests import SubmitExamRequest, TestCreateRequest, TicketSaveRequest
from app.models import User
from app.schemas import (
    ExamPaperOut,
    ExamResultOut,
    ExamSessionOut,
    ExamTicketPaperOut,
    SignedProtocolOut,
    TestCreateOut,
    TestEditOut,
    TestListOut,
    TestSettingsIn,
)

router = APIRouter(prefix="/tests", tags=["tests"])


@router.get("", response_model=TestListOut)
def list_tests(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> TestListOut:
    return dispatch_query(ListTestsQuery(db=db, user=user), TestListOut)


@router.post("", response_model=TestCreateOut, status_code=201)
def create_test(
    form: TestCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
) -> TestCreateOut:
    return dispatch_command(CreateTestCommand(db=db, user=user, form=form), TestCreateOut)


@router.get("/{test_id}", response_model=TestEditOut)
def get_test_for_edit(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
) -> TestEditOut:
    return dispatch_query(GetTestForEditQuery(db=db, test_id=test_id, user=user), TestEditOut)


@router.put("/{test_id}/settings", response_model=TestEditOut)
def update_test_settings(
    test_id: int,
    form: TestSettingsIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
) -> TestEditOut:
    return dispatch_command(
        UpdateTestSettingsCommand(db=db, test_id=test_id, user=user, form=form),
        TestEditOut,
    )


@router.post("/{test_id}/publish", response_model=TestEditOut)
def publish_test(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
) -> TestEditOut:
    return dispatch_command(
        PublishTestCommand(db=db, test_id=test_id, user=user),
        TestEditOut,
    )


@router.delete("/{test_id}", status_code=204)
def delete_test(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
) -> Response:
    get_command_bus().dispatch(
        DeleteTestCommand(db=db, test_id=test_id, user=user)
    )
    return Response(status_code=204)


@router.get("/{test_id}/training", response_model=ExamPaperOut)
def get_training_paper(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> ExamPaperOut:
    return dispatch_query(
        GetTrainingPaperQuery(db=db, test_id=test_id, user=user), ExamPaperOut
    )


@router.post("/{test_id}/training", response_model=ExamResultOut)
def submit_training(
    test_id: int,
    form: SubmitExamRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> ExamResultOut:
    return dispatch_command(
        SubmitTrainingCommand(db=db, test_id=test_id, user=user, form=form), ExamResultOut
    )


@router.post("/{test_id}/exam/session", response_model=ExamSessionOut)
def start_exam_session(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> ExamSessionOut:
    return dispatch_command(
        StartExamSessionCommand(db=db, test_id=test_id, user=user), ExamSessionOut
    )


@router.get("/{test_id}/exam/session", response_model=ExamSessionOut)
def get_exam_session(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> ExamSessionOut:
    return dispatch_query(GetExamSessionQuery(db=db, test_id=test_id, user=user), ExamSessionOut)


@router.get("/{test_id}/exam/tickets/{ticket_id}", response_model=ExamTicketPaperOut)
def get_exam_ticket(
    test_id: int,
    ticket_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> ExamTicketPaperOut:
    return dispatch_command(
        OpenExamTicketCommand(db=db, test_id=test_id, ticket_id=ticket_id, user=user),
        ExamTicketPaperOut,
    )


@router.post("/{test_id}/exam/tickets/{ticket_id}", response_model=ExamSessionOut)
def submit_exam_ticket_answers(
    test_id: int,
    ticket_id: int,
    form: SubmitExamRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> ExamSessionOut:
    return dispatch_command(
        SubmitExamTicketAnswersCommand(
            db=db, test_id=test_id, ticket_id=ticket_id, user=user, form=form
        ),
        ExamSessionOut,
    )


@router.post("/{test_id}/exam/finish", response_model=ExamResultOut)
def finish_exam(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> ExamResultOut:
    return dispatch_command(FinishExamCommand(db=db, test_id=test_id, user=user), ExamResultOut)


@router.get(
    "/{test_id}/exam/attempts/{attempt_id}/result",
    response_model=ExamResultOut,
)
def get_exam_attempt_result(
    test_id: int,
    attempt_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> ExamResultOut:
    return dispatch_query(
        GetExamAttemptResultQuery(
            db=db, test_id=test_id, attempt_id=attempt_id, user=user
        ),
        ExamResultOut,
    )


@router.post(
    "/{test_id}/exam/attempts/{attempt_id}/protocol/sign",
    response_model=SignedProtocolOut,
)
def sign_protocol(
    test_id: int,
    attempt_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
) -> SignedProtocolOut:
    return dispatch_command(
        SignProtocolCommand(db=db, test_id=test_id, attempt_id=attempt_id, signer=user),
        SignedProtocolOut,
    )


@router.get(
    "/{test_id}/exam/attempts/{attempt_id}/protocol",
    response_model=SignedProtocolOut,
)
def get_signed_protocol(
    test_id: int,
    attempt_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> SignedProtocolOut:
    return dispatch_query(
        GetSignedProtocolQuery(
            db=db, test_id=test_id, attempt_id=attempt_id, requester=user
        ),
        SignedProtocolOut,
    )


@router.get("/{test_id}/exam/attempts/{attempt_id}/protocol-draft.pdf")
def get_attempt_protocol_draft_pdf(
    test_id: int,
    attempt_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
) -> Response:
    pdf_bytes = dispatch_query(
        GetAttemptProtocolDraftPdfQuery(
            db=db, test_id=test_id, attempt_id=attempt_id, requester=user
        ),
        bytes,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="protocol_draft_{attempt_id}.pdf"'
        },
    )


@router.get("/{test_id}/exam/attempts/{attempt_id}/protocol-form.pdf")
def get_attempt_protocol_form_pdf(
    test_id: int,
    attempt_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
) -> Response:
    pdf_bytes = dispatch_query(
        GetAttemptProtocolFormPdfQuery(
            db=db, test_id=test_id, attempt_id=attempt_id, requester=user
        ),
        bytes,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="protocol_form_{attempt_id}.pdf"'
        },
    )


@router.get("/{test_id}/exam/attempts/{attempt_id}/protocol.pdf")
def get_signed_protocol_pdf(
    test_id: int,
    attempt_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(login_required)],
) -> Response:
    pdf_bytes = dispatch_query(
        GetSignedProtocolPdfQuery(
            db=db, test_id=test_id, attempt_id=attempt_id, requester=user
        ),
        bytes,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="protocol_{attempt_id}.pdf"'},
    )


@router.post("/{test_id}/tickets", response_model=TestEditOut, status_code=201)
def add_ticket(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
) -> TestEditOut:
    return dispatch_command(AddTicketCommand(db=db, test_id=test_id, user=user), TestEditOut)


@router.put("/{test_id}/tickets/{ticket_id}", response_model=TestEditOut)
def save_ticket(
    test_id: int,
    ticket_id: int,
    form: TicketSaveRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
) -> TestEditOut:
    return dispatch_command(
        SaveTicketCommand(db=db, test_id=test_id, ticket_id=ticket_id, user=user, form=form),
        TestEditOut,
    )


@router.delete("/{test_id}/tickets/{ticket_id}", response_model=TestEditOut)
def delete_ticket(
    test_id: int,
    ticket_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(test_editor_required)],
) -> TestEditOut:
    return dispatch_command(
        DeleteTicketCommand(db=db, test_id=test_id, ticket_id=ticket_id, user=user), TestEditOut
    )
