import { Link, useLocation, useParams } from "react-router-dom";
import DashboardLayout from "../layout/DashboardLayout";
import type { ExamResult } from "../types/api";

export default function ExamResultPage() {
  const { testId } = useParams();
  const location = useLocation();
  const result = location.state?.result as ExamResult | undefined;

  if (!result) {
    return (
      <DashboardLayout active="exam">
        <p className="dash-card-note">Нет данных результата.</p>
        <Link to={`/exam/${testId}`}>Вернуться к экзамену</Link>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout active="exam">
      <section className="dash-hero" style={{ gridTemplateColumns: "1fr auto" }}>
        <div>
          <h1>Результат экзамена</h1>
          <p className="dash-hero-sub">{result.test_title}</p>
          <p className="dash-stat-big dash-stat-percent">{result.percent}%</p>
          <p className={`dash-grade-line ${result.grade_class}`}>оценка: {result.grade}</p>
          <p className="dash-card-note">
            {result.correct} из {result.total} · ошибок: {result.errors} ·{" "}
            {result.passed_exam ? (
              <span className="grade-excellent">сдан</span>
            ) : (
              <span className="grade-bad">не сдан (нужно ≥ {result.min_pass_percent}%)</span>
            )}
          </p>
        </div>
        <Link to="/cabinet" className="dash-exam-btn">
          В кабинет
        </Link>
      </section>
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
