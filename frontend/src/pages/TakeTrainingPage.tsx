import { FormEvent, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { axiosErrorMessage, postReact } from "../api/getReact";
import RichHtml from "../components/RichHtml";
import DashboardLayout from "../layout/DashboardLayout";
import { useGetReact } from "../hooks/useGetReact";
import type { ExamPaper, ExamResult } from "../types/api";
import { labelsForCount, optionFieldsForQuestion } from "../utils/questionOptions";

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
            <h2>{ticket.title?.trim() || `Билет ${ti + 1}`}</h2>
            {ticket.questions.map((q) => {
              const fields = optionFieldsForQuestion(q, ticket.option_count);
              const labels = labelsForCount(ticket.option_count);
              return (
              <div key={q.id} className="dash-question">
                <p>
                  <strong>Вопрос {q.position}.</strong> <RichHtml html={q.text} />
                </p>
                <div className="dash-radio-line">
                  {fields.map(({ label, field }, i) => (
                      <label key={label}>
                        <input type="radio" name={`q_${q.id}`} value={labels[i]} required={i === 0} />
                        {label} — <RichHtml html={q[field]} />
                      </label>
                  ))}
                </div>
              </div>
              );
            })}
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
