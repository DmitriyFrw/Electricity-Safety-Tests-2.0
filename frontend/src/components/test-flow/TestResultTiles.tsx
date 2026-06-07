import { Link } from "react-router-dom";
import type { ExamResult, QuestionResult } from "../../types/api";

type Props = {
  questions: QuestionResult[];
  reviewBasePath: string;
  result: ExamResult;
};

export default function TestResultTiles({ questions, reviewBasePath, result }: Props) {
  const byTicket = new Map<number, QuestionResult[]>();
  for (const q of questions) {
    const list = byTicket.get(q.ticket_position) ?? [];
    list.push(q);
    byTicket.set(q.ticket_position, list);
  }

  const ticketPositions = [...byTicket.keys()].sort((a, b) => a - b);

  return (
    <>
      {ticketPositions.map((pos) => {
        const rows = (byTicket.get(pos) ?? []).sort(
          (a, b) => a.question_position - b.question_position
        );
        const title = rows[0]?.ticket_title?.trim() || `Билет ${pos}`;
        return (
          <section key={pos} className="dash-page-card test-result-ticket-block">
            <h2 className="test-result-ticket-title">{title}</h2>
            <ul className="test-result-tile-grid">
              {rows.map((q) => (
                <li key={q.question_id}>
                  <Link
                    to={`${reviewBasePath}/q/${q.question_id}`}
                    state={{ result }}
                    className={`test-result-tile ${
                      q.is_correct ? "test-result-tile-correct" : "test-result-tile-wrong"
                    }`}
                  >
                    <span className="test-result-tile-num">{q.question_position}</span>
                    <span className="test-result-tile-label">
                      {q.is_correct ? "верно" : "ошибка"}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </>
  );
}
