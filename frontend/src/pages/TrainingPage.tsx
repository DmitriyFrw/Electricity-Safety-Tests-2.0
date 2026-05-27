import { Link } from "react-router-dom";
import DashboardLayout from "../layout/DashboardLayout";
import { useGetReact } from "../hooks/useGetReact";
import type { TestListItem } from "../types/api";

export default function TrainingPage() {
  const { data, error, loading } = useGetReact<{ items: TestListItem[] }>("/tests");
  const tests = data?.items ?? [];

  return (
    <DashboardLayout active="training">
      <div className="dash-page-card">
        <h1>Обучение</h1>
        <p className="dash-card-note">Выберите тест для изучения билетов</p>
      </div>
      {error && <p className="auth-error">{error}</p>}
      {loading && <p className="dash-card-note">Загрузка…</p>}
      <div className="dash-table-wrap">
        <table className="dash-table">
          <thead>
            <tr>
              <th>Тест</th>
              <th>Автор</th>
              <th>Билетов</th>
              <th>Статус</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {tests.map((t) => (
              <tr key={t.id}>
                <td>{t.title}</td>
                <td>{t.author_username}</td>
                <td>{t.ticket_count}</td>
                <td>{t.ready ? <span className="dash-pill-ok">Готов</span> : <span className="dash-pill-draft">Черновик</span>}</td>
                <td>
                  {t.ready && <Link to={`/exam/${t.id}`}>Пройти</Link>}
                  {t.is_owner && (
                    <>
                      {" "}
                      <Link to={`/tests/${t.id}/edit`}>Редактировать</Link>
                    </>
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
