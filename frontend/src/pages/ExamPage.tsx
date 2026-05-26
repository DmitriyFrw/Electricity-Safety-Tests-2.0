import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import DashboardLayout from "../layout/DashboardLayout";
import type { TestListItem } from "../types/api";

export default function ExamPage() {
  const [tests, setTests] = useState<TestListItem[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listTests()
      .then(setTests)
      .catch((e) => setError(e instanceof Error ? e.message : "Ошибка"));
  }, []);

  const firstReady = tests.find((t) => t.ready);

  return (
    <DashboardLayout active="exam">
      <div className="dash-page-card">
        <h1>Экзамен</h1>
        <p className="dash-card-note">Выберите тест для сдачи</p>
        {firstReady && (
          <Link to={`/exam/${firstReady.id}`} className="dash-exam-btn">
            Сдать экзамен
          </Link>
        )}
      </div>
      {error && <p className="auth-error">{error}</p>}
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
