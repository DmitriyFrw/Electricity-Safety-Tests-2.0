from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.api.mappers import exam_result_out
from app.models import Attempt, Test, Ticket
from app.repositories import ProtocolRepository
from app.schemas import ExamResultOut
from app.services.attempts.scoring import (
    AttemptScore,
    build_exam_question_result_rows,
    build_ticket_result_rows,
    score_attempt,
    score_exam_questions,
)
from app.support.exam_composition import load_exam_questions, parse_composition


def build_exam_result_out(db: Session, *, attempt: Attempt, test: Test) -> ExamResultOut:
    db.refresh(attempt, attribute_names=["user_answers"])
    composition = parse_composition(attempt.exam_ticket_order)
    protocol = ProtocolRepository.get_by_attempt_id(db, attempt.id)

    if composition:
        ticket = db.get(Ticket, composition.ticket_id)
        if not ticket:
            raise ValueError("Билет экзамена не найден")
        questions = load_exam_questions(db, composition.question_ids)
        summary: AttemptScore = score_exam_questions(questions, attempt.user_answers)
        by_q = {ua.question_id: ua.selected_index for ua in attempt.user_answers}
        t_correct: defaultdict[int, int] = defaultdict(int)
        t_total: defaultdict[int, int] = defaultdict(int)
        t_total[ticket.id] = len(questions)
        for q in questions:
            sel = by_q.get(q.id)
            if sel is not None and sel == q.correct_index:
                t_correct[ticket.id] += 1
        ticket_rows = build_ticket_result_rows([ticket], t_correct, t_total)
        question_rows = build_exam_question_result_rows(ticket, questions, attempt.user_answers)
    else:
        summary = score_attempt(db, attempt)
        ticket_rows = []
        question_rows = []

    return exam_result_out(
        test,
        summary,
        ticket_rows,
        attempt_id=attempt.id,
        protocol_signed=protocol is not None,
        question_rows=question_rows,
    )
