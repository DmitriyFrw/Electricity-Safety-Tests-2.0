import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api } from "../api/client";
import { axiosErrorMessage } from "../api/getReact";
import TestResultTiles from "../components/test-flow/TestResultTiles";
import DashboardLayout from "../layout/DashboardLayout";
import type { ExamResult } from "../types/api";

export default function TrainingResultPage() {
  const { testId, attemptId } = useParams();
  const location = useLocation();
  const stateResult = location.state?.result as ExamResult | undefined;
  const tid = Number(testId);
  const aid = Number(attemptId);
  const hasIds = Number.isFinite(tid) && Number.isFinite(aid);
  const [result, setResult] = useState<ExamResult | undefined>(stateResult);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(!stateResult && hasIds);

  useEffect(() => {
    if (stateResult) {
      setResult(stateResult);
      setLoading(false);
      return;
    }
    if (!hasIds) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setLoadError("");
    void api
      .getTrainingResult(tid, aid)
      .then((data) => {
        if (!cancelled) setResult(data);
      })
      .catch((err) => {
        if (!cancelled) setLoadError(axiosErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [stateResult, hasIds, tid, aid]);

  if (loading) {
    return (
      <DashboardLayout active="training">
        <p className="dash-card-note">Загрузка…</p>
      </DashboardLayout>
    );
  }

  if (loadError) {
    return (
      <DashboardLayout active="training">
        <p className="auth-error">{loadError}</p>
        <Link to={`/training/${testId ?? ""}`}>Вернуться к тренировке</Link>
      </DashboardLayout>
    );
  }

  if (!result || !hasIds) {
    return (
      <DashboardLayout active="training">
        <p className="dash-card-note">Нет данных результата.</p>
        <Link to={`/training/${testId ?? ""}`}>Вернуться к тренировке</Link>
      </DashboardLayout>
    );
  }

  const questions = result.question_results ?? [];
  const reviewBasePath = `/training/${tid}/result/${aid}`;

  return (
    <DashboardLayout active="training">
      <section className="dash-hero">
        <div>
          <h1>Результат тренировки</h1>
          <p className="dash-hero-sub">{result.test_title}</p>
          <p className="dash-stat-big dash-stat-percent">{result.percent}%</p>
          <p className={`dash-grade-line ${result.grade_class}`}>оценка: {result.grade}</p>
          <p className="dash-card-note">
            {result.correct} из {result.total} · ошибок: {result.errors}
          </p>
        </div>
        <Link to="/training" className="dash-exam-btn">
          К обучению
        </Link>
      </section>

      {questions.length > 0 && (
        <TestResultTiles
          questions={questions}
          reviewBasePath={reviewBasePath}
          result={result}
        />
      )}

      {result.ticket_rows.length > 0 && (
        <div className="dash-table-wrap">
          <table className="dash-table">
            <thead>
              <tr>
                <th>Билет</th>
                <th>Правильно</th>
                <th>%</th>
                <th>Оценка</th>
              </tr>
            </thead>
            <tbody>
              {result.ticket_rows.map((r) => (
                <tr key={r.n}>
                  <td>№{r.n}</td>
                  <td>
                    {r.correct}/{r.total}
                  </td>
                  <td>{r.percent}%</td>
                  <td className={r.grade_class}>{r.grade}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </DashboardLayout>
  );
}
