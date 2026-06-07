import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { axiosErrorMessage, postReact } from "../api/getReact";
import PaginatedTestFlow, { type AnswersMap } from "../components/test-flow/PaginatedTestFlow";
import DashboardLayout from "../layout/DashboardLayout";
import { useGetReact } from "../hooks/useGetReact";
import type { ExamPaper, ExamResult } from "../types/api";

export default function TakeTrainingPage() {
  const { testId } = useParams();
  const navigate = useNavigate();
  const id = Number(testId);
  const path = id ? `/tests/${id}/training` : null;
  const { data: paper, error: loadError, loading: loadPaper } = useGetReact<ExamPaper>(path, Boolean(id));
  const [submitError, setSubmitError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onComplete = async (answers: AnswersMap) => {
    if (!paper) return;
    setSubmitting(true);
    setSubmitError("");
    const payload = Object.entries(answers).map(([question_id, value]) => ({
      question_id: Number(question_id),
      value,
    }));
    try {
      const result = await postReact<ExamResult>(`/tests/${paper.id}/training`, { answers: payload });
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
      <PaginatedTestFlow
        tickets={paper.tickets}
        testTitle={paper.title}
        subtitle="Тренировка — без ограничения по времени"
        cancelHref="/training"
        onComplete={onComplete}
        completing={submitting}
        completeError={submitError}
        finishLabel="Завершить тест"
        allowEarlyFinish
      />
    </DashboardLayout>
  );
}
