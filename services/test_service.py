from __future__ import annotations

from sqlalchemy.orm import Session

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
)
from app.services.tests import (
    TestCatalogService,
    TestEditorService,
    TestExamService,
    TestProtocolService,
    TestTrainingService,
)


class TestService:
    """Фасад: делегирует в модульные сервисы (catalog / editor / training / exam / protocols)."""

    list_tests = staticmethod(TestCatalogService.list_tests)
    create_test = staticmethod(TestCatalogService.create_test)

    get_test_for_edit = staticmethod(TestEditorService.get_test_for_edit)
    add_ticket = staticmethod(TestEditorService.add_ticket)
    save_ticket = staticmethod(TestEditorService.save_ticket)
    delete_ticket = staticmethod(TestEditorService.delete_ticket)

    get_training_paper = staticmethod(TestTrainingService.get_training_paper)
    submit_training = staticmethod(TestTrainingService.submit_training)

    start_exam_session = staticmethod(TestExamService.start_exam_session)
    get_exam_session = staticmethod(TestExamService.get_exam_session)
    get_exam_ticket = staticmethod(TestExamService.get_exam_ticket)
    submit_exam_ticket_answers = staticmethod(TestExamService.submit_exam_ticket_answers)
    finish_exam = staticmethod(TestExamService.finish_exam)

    sign_protocol = staticmethod(TestProtocolService.sign_protocol)
    get_signed_protocol = staticmethod(TestProtocolService.get_signed_protocol)
    get_signed_protocol_pdf = staticmethod(TestProtocolService.get_signed_protocol_pdf)
