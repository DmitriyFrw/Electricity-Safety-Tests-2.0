import { Link, useLocation, useParams } from "react-router-dom";
import TestResultTiles from "../components/test-flow/TestResultTiles";
import DashboardLayout from "../layout/DashboardLayout";
import type { ExamResult } from "../types/api";

export default function TrainingResultPage() {
  const { testId } = useParams();
  const location = useLocation();
  const result = location.state?.result as ExamResult | undefined;

  if (!result) {
    return (
      <DashboardLayout active="training">
        <p className="dash-card-note">Нет данных результата.</p>
        <Link to={`/training/${testId}`}>Вернуться к тренировке</Link>
      </DashboardLayout>
    );
  }

  const questions = result.question_results ?? [];

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
          reviewBasePath={`/training/${testId}/result`}
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
