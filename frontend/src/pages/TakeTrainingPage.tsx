import { FormEvent, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { axiosErrorMessage, postReact } from "../api/getReact";
import DashboardLayout from "../layout/DashboardLayout";
import { useGetReact } from "../hooks/useGetReact";
import type { ExamPaper, ExamResult } from "../types/api";

const LABELS = ["A", "B", "C", "D"] as const;

export default function TakeTrainingPage() {
  const { testId } = useParams();
  const navigate = useNavigate();
  const id = Number(testId);
  const path = id ? `/tests/${id}/training` : null;
  const { data: paper, error: loadError, loading: loadPaper } = useGetReact<ExamPaper>(path, Boolean(id));
  const [submitError, setSubmitError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!paper) return;
    setSubmitting(true);
    setSubmitError("");
    const fd = new FormData(e.target as HTMLFormElement);
    const answers: { question_id: number; value: string }[] = [];
    paper.tickets.forEach((ticket) =>
      ticket.questions.forEach((q) => {
        const v = fd.get(`q_${q.id}`);
        if (v) answers.push({ question_id: q.id, value: String(v) });
      })
    );
    try {
      const result = await postReact<ExamResult>(`/tests/${paper.id}/training`, { answers });
      navigate(`/training/${paper.id}/result`, { state: { result } });
    } catch (err) {
      setSubmitError(axiosErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (loadError && !paper) {
    return (
      <DashboardLayout active="training">
        <p className="auth-error">{loadError}</p>
        <Link to="/training">← К обучению</Link>
      </DashboardLayout>
    );
  }
  if (loadPaper || !paper) {
    return (
      <DashboardLayout active="training">
        <p className="dash-card-note">Загрузка…</p>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout active="training">
      <div className="dash-page-card">
        <h1>{paper.title}</h1>
        <p className="dash-card-note">Тренировка — без ограничения по времени</p>
      </div>
      <form onSubmit={onSubmit}>
        {paper.tickets.map((ticket, ti) => (
          <div key={ticket.id} className="test-question-card dash-no-copy">
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
                        <input type="radio" name={`q_${q.id}`} value={letter} required={i === 0} />
                        {letter} — {opts[i]}
                      </label>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        ))}
        {submitError && <p className="auth-error">{submitError}</p>}
        <button type="submit" className="dash-exam-btn" disabled={submitting} style={{ border: "none", cursor: "pointer" }}>
          {submitting ? "Отправка…" : "Завершить тренировку"}
        </button>
        <Link to="/training" className="dash-card-link" style={{ marginLeft: "1rem" }}>
          Отмена
        </Link>
      </form>
    </DashboardLayout>
  );
}
