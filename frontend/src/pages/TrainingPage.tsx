import { Link } from "react-router-dom";
import { safetyGroupLabel } from "../constants/safetyGroups";
import DashboardLayout from "../layout/DashboardLayout";
import { useGetReact } from "../hooks/useGetReact";
import type { Dashboard, TestListItem } from "../types/api";
import { formatDateRu } from "../utils/format";

export default function TrainingPage() {
  const { data, error, loading } = useGetReact<{ items: TestListItem[] }>("/tests");
  const { data: dashboard } = useGetReact<Dashboard>("/dashboard");
  const tests = data?.items ?? [];
  const attempts = dashboard?.attempts ?? [];
  const attemptsTotal = dashboard?.attempts_total ?? attempts.length;
  const attemptsTruncated = attemptsTotal > attempts.length;

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
              <th>Группа</th>
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
                <td>{safetyGroupLabel(t.safety_group)}</td>
                <td>{t.author_username}</td>
                <td>{t.ticket_count}</td>
                <td>{t.ready ? <span className="dash-pill-ok">Готов</span> : <span className="dash-pill-draft">Черновик</span>}</td>
                <td>
                  <div className="dash-table-actions">
                    {t.ready && (
                      <Link to={`/training/${t.id}`} className="btn btn-primary btn-sm">
                        Пройти
                      </Link>
                    )}
                    {t.can_edit && (
                      <Link to={`/constructor/${t.id}`} className="btn btn-outline btn-sm">
                        Редактировать
                      </Link>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {attempts.length > 0 && (
        <section className="dash-section dash-section--glass">
          <h2 className="dash-section-title">История пройденных тестов</h2>
          {attemptsTruncated && (
            <p className="dash-card-note">
              Показаны последние {attempts.length} из {attemptsTotal} попыток
            </p>
          )}
          <div className="dash-table-wrap">
            <table className="dash-table">
              <thead>
                <tr>
                  <th>Тест</th>
                  <th>Дата</th>
                  <th>Результат</th>
                  <th>Ошибки</th>
                  <th>%</th>
                  <th>Оценка</th>
                </tr>
              </thead>
              <tbody>
                {attempts.map((a) => (
                  <tr key={a.attempt_id}>
                    <td>{a.test_title}</td>
                    <td>{formatDateRu(a.finished_at)}</td>
                    <td>
                      {a.correct}/{a.total}
                    </td>
                    <td>{a.errors}</td>
                    <td>{a.percent}%</td>
                    <td className={a.grade_class}>{a.grade}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </DashboardLayout>
  );
}
