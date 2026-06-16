from __future__ import annotations

from app.models import Question, Ticket


def add_questions_to_ticket(
    ticket: Ticket,
    *,
    count: int = 10,
    correct_index: int = 0,
) -> None:
    for pos in range(1, count + 1):
        ticket.questions.append(
            Question(
                position=pos,
                text=f"Q{pos}",
                correct_index=correct_index,
                correct_indexes=str(correct_index),
                option_a="A",
                option_b="B",
                option_c="C",
                option_d="D",
            )
        )
