import { Link } from "react-router-dom";
import DashboardLayout from "../layout/DashboardLayout";
import { useGetReact } from "../hooks/useGetReact";
import type { TestListItem } from "../types/api";
import { EXAM_TICKET_MINUTES } from "../utils/exam";

export default function ExamPage() {
  const { data, error, loading } = useGetReact<{ items: TestListItem[] }>("/tests");
  const tests = data?.items ?? [];

  const firstReady = tests.find((t) => t.ready);

  return (
    <DashboardLayout active="exam">
      <div className="dash-page-card">
        <h1>Экзамен</h1>
        <p className="dash-card-note">
          На каждый билет — {EXAM_TICKET_MINUTES} минут. Тренировка без ограничения по времени — в разделе «Обучение».
        </p>
        {firstReady && (
          <Link to={`/exam/${firstReady.id}`} className="dash-exam-btn">
            Сдать экзамен
          </Link>
        )}
      </div>
      {error && <p className="auth-error">{error}</p>}
      {loading && <p className="dash-card-note">Загрузка…</p>}
      <div className="dash-table-wrap">
        <table className="dash-table">
          <thead>
            <tr>
              <th>Название</th>
              <th>Билетов</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {tests.map((t) => (
              <tr key={t.id}>
                <td>{t.title}</td>
                <td>{t.ticket_count}</td>
                <td>
                  {t.ready ? (
                    <Link to={`/exam/${t.id}`}>Пройти</Link>
                  ) : (
                    <span className="dash-pill-draft">Черновик</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DashboardLayout>
  );
}
