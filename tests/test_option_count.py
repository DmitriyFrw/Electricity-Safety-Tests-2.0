from app.models import Question, Ticket
from app.support.validation import ticket_is_complete


def _question(position: int, **opts: str) -> Question:
    return Question(
        id=position,
        ticket_id=1,
        position=position,
        text="Текст вопроса",
        correct_index=0,
        option_a=opts.get("a", "A"),
        option_b=opts.get("b", "B"),
        option_c=opts.get("c", ""),
        option_d=opts.get("d", ""),
    )


def test_ticket_complete_with_two_options():
    ticket = Ticket(id=1, test_id=1, position=1, option_count=2)
    ticket.questions = [_question(i) for i in range(1, 11)]
    assert ticket_is_complete(ticket)


def test_ticket_incomplete_when_third_option_required():
    ticket = Ticket(id=1, test_id=1, position=1, option_count=3)
    ticket.questions = [_question(i) for i in range(1, 11)]
    assert not ticket_is_complete(ticket)
