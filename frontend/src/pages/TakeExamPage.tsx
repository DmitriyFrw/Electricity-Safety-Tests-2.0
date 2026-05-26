import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import DashboardLayout from "../layout/DashboardLayout";
import type { ExamPaper } from "../types/api";

const LABELS = ["A", "B", "C", "D"] as const;

export default function TakeExamPage() {
  const { testId } = useParams();
  const navigate = useNavigate();
  const id = Number(testId);
  const [paper, setPaper] = useState<ExamPaper | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    api
      .getExamPaper(id)
      .then(setPaper)
      .catch((e) => setError(e instanceof Error ? e.message : "Ошибка"));
  }, [id]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!paper) return;
    setLoading(true);
    const fd = new FormData(e.target as HTMLFormElement);
    const answers: { question_id: number; value: string }[] = [];
    paper.tickets.forEach((ticket) =>
      ticket.questions.forEach((q) => {
        const v = fd.get(`q_${q.id}`);
        if (v) answers.push({ question_id: q.id, value: String(v) });
      })
    );
    try {
      const result = await api.submitExam(paper.id, answers);
      navigate(`/exam/${paper.id}/result`, { state: { result } });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка отправки");
    } finally {
      setLoading(false);
    }
  };

  if (error && !paper) {
    return (
      <DashboardLayout active="exam">
        <p className="auth-error">{error}</p>
        <Link to="/exam">← К каталогу</Link>
      </DashboardLayout>
    );
  }
  if (!paper) {
    return (
      <DashboardLayout active="exam">
        <p className="dash-card-note">Загрузка…</p>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout active="exam">
      <div className="dash-page-card">
        <h1>{paper.title}</h1>
        <p className="dash-card-note">
          Для сдачи нужно ≥ {paper.min_pass_percent}% правильных ответов
        </p>
      </div>
      <form onSubmit={onSubmit}>
        {paper.tickets.map((ticket, ti) => (
          <div key={ticket.id} className="dash-page-card dash-ticket">
            <h2>Билет {ti + 1}</h2>
            {ticket.questions.map((q) => (
              <div key={q.id} className="dash-question">
                <p>
                  <strong>Вопрос {q.position}.</strong> {q.text}
                </p>
                <div className="dash-radio-line">
                  {LABELS.map((letter, i) => {
                    const opts = [q.option_a, q.option_b, q.option_c, q.option_d];
                    return (
                      <label key={letter}>
                        <input
                          type="radio"
                          name={`q_${q.id}`}
                          value={letter}
                          required={i === 0}
                        />
                        {letter} — {opts[i]}
                      </label>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        ))}
        {error && <p className="auth-error">{error}</p>}
        <button type="submit" className="dash-exam-btn" disabled={loading} style={{ border: "none", cursor: "pointer" }}>
          {loading ? "Отправка…" : "Отправить ответы"}
        </button>
        <Link to="/exam" className="dash-card-link" style={{ marginLeft: "1rem" }}>
          Отмена
        </Link>
      </form>
    </DashboardLayout>
  );
}
