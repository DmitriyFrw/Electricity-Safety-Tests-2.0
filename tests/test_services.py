from __future__ import annotations

from sqlalchemy import event

from app.dto import ExportRequestDTO
from app.models import Attempt, Question, Test, Ticket, User
from app.repositories import TestRepository
from app.services.exports import ExportService


def test_export_service_creates_exam_csv(db_session):
    user = User(username="svc_u", password_hash="x", role="kot")
    db_session.add(user)
    db_session.flush()
    test = Test(author_id=user.id, title="SVC", description=None)
    db_session.add(test)
    db_session.flush()
    db_session.add(Attempt(user_id=user.id, test_id=test.id, mode="exam"))
    db_session.commit()

    task_id = ExportService.create_exam_results_export(ExportRequestDTO(user_id=user.id))
    for _ in range(50):
        task = ExportService.get_task(task_id)
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

    def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
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
