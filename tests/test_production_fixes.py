from __future__ import annotations

from app.cache import _caches, invalidate_cache
from app.constants import ROLE_KOT
from app.cqrs.handlers.tests_catalog import _test_list_cache_key
from app.cqrs.messages.tests import ListTestsQuery
from app.models import Attempt, Question, Test, Ticket, User, UserAnswer
from app.services.exams.result import build_exam_result_out
from app.support.answers import encode_correct_indexes, set_user_answer_from_raw
from app.support.exam_composition import serialize_composition, ExamComposition
from app.support.file_types import sniff_mime_type, validate_wiki_upload


def _user(uid: int, role: str, safety_group: str | None = "II") -> User:
    return User(id=uid, username=f"u{uid}", password_hash="x", role=role, safety_group=safety_group)


def test_test_list_cache_key_includes_role_and_safety_group():
    kot_ii = _user(1, ROLE_KOT, "II")
    kot_iii = _user(1, ROLE_KOT, "III")
    ezh = _user(1, "ezh", None)

    key_ii = _test_list_cache_key(ListTestsQuery(db=None, user=kot_ii))  # type: ignore[arg-type]
    key_iii = _test_list_cache_key(ListTestsQuery(db=None, user=kot_iii))  # type: ignore[arg-type]
    key_ezh = _test_list_cache_key(ListTestsQuery(db=None, user=ezh))  # type: ignore[arg-type]

    assert key_ii != key_iii
    assert "group:II" in key_ii
    assert "group:III" in key_iii
    assert "role:ezh" in key_ezh


def test_invalidate_cache_clears_test_list():
    from cachetools import TTLCache

    _caches["test_list"] = TTLCache(maxsize=16, ttl=60)
    _caches["test_list"]["user:1:role:kot:group:II"] = "a"
    _caches["test_list"]["user:2:role:kot:group:II"] = "b"

    invalidate_cache("test_list")

    assert len(_caches["test_list"]) == 0


def test_exam_result_ticket_rows_multi_choice(db_session):
    user = User(username="mc_user", password_hash="x", role=ROLE_KOT, safety_group="II")
    db_session.add(user)
    db_session.flush()

    test = Test(author_id=user.id, title="MC", safety_group="II", published=True)
    ticket = Ticket(position=1, option_count=4)
    q = Question(
        position=1,
        text="Q1",
        correct_index=0,
        correct_indexes=encode_correct_indexes([0, 1]),
        option_a="a",
        option_b="b",
        option_c="c",
        option_d="d",
    )
    ticket.questions.append(q)
    test.tickets.append(ticket)
    db_session.add(test)
    db_session.flush()

    attempt = Attempt(
        user_id=user.id,
        test_id=test.id,
        mode="exam",
        exam_ticket_order=serialize_composition(ExamComposition(ticket_id=ticket.id, question_ids=[q.id])),
    )
    db_session.add(attempt)
    db_session.flush()

    ua = UserAnswer(attempt_id=attempt.id, question_id=q.id, selected_index=None)
    set_user_answer_from_raw(ua, "A,B", option_count=4)
    db_session.add(ua)
    db_session.commit()

    result = build_exam_result_out(db_session, attempt=attempt, test=test)

    assert result.ticket_rows[0].correct == 1
    assert result.ticket_rows[0].total == 1
    assert result.percent == 100.0


def test_sniff_mime_type_png():
    assert sniff_mime_type(b"\x89PNG\r\n\x1a\n") == "image/png"


def test_validate_wiki_upload_rejects_mismatch():
    try:
        validate_wiki_upload("evil.jpg", b"\x89PNG\r\n\x1a\n")
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "не соответствует" in str(e).lower() or "соответствует" in str(e).lower()
