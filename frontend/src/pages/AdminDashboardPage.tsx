import { Link } from "react-router-dom";
import AdminLayout from "../layout/AdminLayout";
import { useGetReact } from "../hooks/useGetReact";
import type { AdminStats } from "../types/api";
import { formatDateRu } from "../utils/format";
import {
  barHeightPercent,
  donutGradient,
  gradeLegend,
  monthLabel,
  monthlyChartMax,
} from "../utils/adminCharts";

export default function AdminDashboardPage() {
  const { data: stats, error, loading } = useGetReact<AdminStats>("/admin/stats");

  const monthlyMax = monthlyChartMax(stats?.monthly_results ?? []);
  const legend = gradeLegend(stats?.grade_distribution ?? []);

  return (
    <AdminLayout>
      <h1>Панель управления</h1>

      {error && <p className="auth-error">{error}</p>}
      {loading && <p>Загрузка…</p>}

      {stats && (
        <>
          <div className="admin-stats">
            <div className="admin-stat-card">
              <div className="admin-stat-card__label">Пользователи</div>
              <div className="admin-stat-card__value">{stats.users_count}</div>
            </div>
            <div className="admin-stat-card">
              <div className="admin-stat-card__label">Тесты</div>
              <div className="admin-stat-card__value">{stats.tests_count}</div>
            </div>
            <div className="admin-stat-card">
              <div className="admin-stat-card__label">Экзамены сданы</div>
              <div className="admin-stat-card__value">{stats.exams_passed_count}</div>
            </div>
            <div className="admin-stat-card">
              <div className="admin-stat-card__label">Средний результат</div>
              <div className="admin-stat-card__value">{stats.average_percent}%</div>
            </div>
          </div>

          <div className="admin-charts">
            <div className="admin-chart-card">
              <h2>Результаты по месяцам</h2>
              <div className="admin-bar-chart">
                {stats.monthly_results.map((row) => (
                  <div key={`${row.year}-${row.month}`} className="admin-bar-chart__col">
                    <div
                      className="admin-bar-chart__bar"
                      style={{ height: `${barHeightPercent(row.average_percent, monthlyMax)}%` }}
                      title={`${row.average_percent}% (${row.attempt_count} попыток)`}
                    />
                    <span className="admin-bar-chart__label">{monthLabel(row.month)}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="admin-chart-card">
              <h2>Распределение результатов</h2>
              <div className="admin-donut">
                <div
                  className="admin-donut__ring"
                  style={{ background: donutGradient(stats.grade_distribution) }}
                  aria-hidden="true"
                />
                <div className="admin-donut__legend">
                  {legend.length > 0 ? (
                    legend.map((item) => (
                      <div key={item.grade} className="admin-donut__legend-item">
                        <span className="admin-donut__dot" style={{ background: item.color }} />
                        {item.label} — {item.percent}% ({item.count})
                      </div>
                    ))
                  ) : (
                    <div className="admin-donut__legend-item">Нет завершённых попыток</div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="admin-bottom-row">
            <div className="admin-activity">
              <h2>Недавняя активность</h2>
              <ul className="admin-activity__list">
                {stats.recent_activity.map((row, idx) => (
                  <li key={`${row.finished_at}-${idx}`} className="admin-activity__item">
                    <span>
                      {row.user_display_name} — {row.test_title} ({row.grade})
                    </span>
                    <span>
                      {row.percent}% · {formatDateRu(row.finished_at)}
                    </span>
                  </li>
                ))}
                {!stats.recent_activity.length && (
                  <li className="admin-activity__item">Нет недавней активности</li>
                )}
              </ul>
            </div>
            <div className="admin-quick-actions">
              <Link to="/constructor?create=1" className="mockup-btn mockup-btn--primary">
                + Создать тест
              </Link>
              <Link to="/admin/users" className="mockup-btn mockup-btn--outline">
                Управление пользователями
              </Link>
            </div>
          </div>
        </>
      )}
    </AdminLayout>
  );
}
