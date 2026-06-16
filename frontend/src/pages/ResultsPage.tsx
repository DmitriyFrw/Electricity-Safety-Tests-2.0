import TopNavLayout from "../layout/TopNavLayout";
import { useGetReact } from "../hooks/useGetReact";
import type { Dashboard } from "../types/api";
import { formatDateRu } from "../utils/format";

export default function ResultsPage() {
  const { data, error, loading } = useGetReact<Dashboard>("/dashboard");
  const attempts = data?.attempts ?? [];
  const attemptsTotal = data?.attempts_total ?? attempts.length;
  const attemptsTruncated = attemptsTotal > attempts.length;

  return (
    <TopNavLayout active="results">
      <header className="mockup-page-header">
        <h1>Результаты</h1>
        <p>История ваших тренировок и экзаменов</p>
      </header>

      {error && <p className="auth-error">{error}</p>}
      {loading && <p>Загрузка…</p>}

      {!loading && attempts.length === 0 && (
        <p className="mockup-page-header p">Пока нет завершённых попыток.</p>
      )}

      {attempts.length > 0 && (
        <>
          {attemptsTruncated && (
            <p className="mockup-page-header p">
              Показаны последние {attempts.length} из {attemptsTotal} попыток
            </p>
          )}
          <div className="results-table-wrap">
            <table className="results-table">
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
                    <td className="results-percent">{a.percent}%</td>
                    <td className={a.grade_class}>{a.grade}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </TopNavLayout>
  );
}
