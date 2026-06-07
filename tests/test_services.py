from __future__ import annotations

from sqlalchemy import event

from app.cqrs import get_command_bus, get_query_bus
from app.cqrs.messages.exports import CreateExamResultsExportCommand, GetExportTaskQuery
from app.dto import ExportRequestDTO
from app.models import Attempt, Question, Test, Ticket, User
from app.repositories import TestRepository


def test_export_service_creates_exam_csv(db_session):
    user = User(username="svc_u", password_hash="x", role="kot")
    db_session.add(user)
    db_session.flush()
    test = Test(author_id=user.id, title="SVC", description=None)
    db_session.add(test)
    db_session.flush()
    db_session.add(Attempt(user_id=user.id, test_id=test.id, mode="exam"))
    db_session.commit()

    req = ExportRequestDTO.model_validate({"user_id": user.id, "kind": "exam_results"})
    task_id = get_command_bus().dispatch(CreateExamResultsExportCommand(request=req))
    for _ in range(50):
        task = get_query_bus().dispatch(GetExportTaskQuery(task_id=task_id))
        if task and task.status == "done":
            assert task.payload is not None
            assert b"attempt_id,test_id,mode" in task.payload
            return
    raise AssertionError("Export task was not completed in time")


def test_repository_avoids_n_plus_one(db_session):
    author = User(username="n1_author", password_hash="x", role="ezh")
    db_session.add(author)
    db_session.flush()
    test = Test(author_id=author.id, title="N+1 test", description=None)
    ticket = Ticket(position=1)
    test.tickets.append(ticket)
    for pos in range(1, 11):
        ticket.questions.append(
            Question(
                position=pos,
                text=f"Q{pos}",
                correct_index=0,
                option_a="a",
                option_b="b",
                option_c="c",
                option_d="d",
            )
        )
    db_session.add(test)
    db_session.commit()

    queries: list[str] = []

    def _before_cursor_execute(
        conn: object,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        queries.append(statement)

    event.listen(db_session.bind, "before_cursor_execute", _before_cursor_execute)
    try:
        rows = TestRepository.list_all(db_session)
        assert rows
        # Access related fields that would trigger N+1 without eager loading.
        _ = [(x.author.username, len(x.tickets)) for x in rows]
    finally:
        event.remove(db_session.bind, "before_cursor_execute", _before_cursor_execute)

    # 1 query tests + 1 authors/tickets prefetch bucket ~= small bounded number.
    assert len(queries) <= 4


def _make_two_ticket_test(db_session, *, author_id: int) -> Test:
    test = Test(author_id=author_id, title="Early finish", description=None, published=True)
    for tpos in (1, 2):
        ticket = Ticket(position=tpos)
        for qpos in range(1, 11):
            ticket.questions.append(
                Question(
                    position=qpos,
                    text=f"T{tpos}Q{qpos}",
                    correct_index=0,
                    option_a="a",
                    option_b="b",
                    option_c="c",
                    option_d="d",
                )
            )
        test.tickets.append(ticket)
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)
    return test


def test_training_early_finish_scores_only_attempted_tickets(db_session):
    from app.services.attempts.scoring import submit_test_attempt_with_answers

    user = User(username="early_user", password_hash="x", role="ezh")
    db_session.add(user)
    db_session.flush()
    test = _make_two_ticket_test(db_session, author_id=user.id)
    tickets = sorted(test.tickets, key=lambda t: t.position)
    answers: dict[int, str] = {}
    for q in tickets[0].questions:
        answers[q.id] = "a" if q.position <= 5 else "b"

    _, summary, ticket_rows = submit_test_attempt_with_answers(
        db_session,
        user_id=user.id,
        test=test,
        answers=answers,
    )

    assert summary.correct == 5
    assert summary.total == 10
    assert summary.percent == 50.0
    assert len(ticket_rows) == 1
