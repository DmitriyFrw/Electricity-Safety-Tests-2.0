import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { SAFETY_GROUPS, safetyGroupLabel } from "../constants/safetyGroups";
import TopNavLayout from "../layout/TopNavLayout";
import { useGetReact } from "../hooks/useGetReact";
import type { AttemptRow, Dashboard, TestListItem } from "../types/api";

function bestPercentForTest(attempts: AttemptRow[], testId: number): number {
  const related = attempts.filter((a) => a.test_id === testId);
  if (!related.length) return 0;
  return Math.max(...related.map((a) => a.percent));
}

export default function TrainingPage() {
  const [filter, setFilter] = useState<string>("all");
  const { data, error, loading } = useGetReact<{ items: TestListItem[] }>("/tests");
  const { data: dashboard } = useGetReact<Dashboard>("/dashboard");
  const tests = data?.items ?? [];
  const attempts = dashboard?.attempts ?? [];

  const readyTests = useMemo(() => tests.filter((t) => t.ready), [tests]);

  const filtered = useMemo(() => {
    if (filter === "all") return readyTests;
    return readyTests.filter((t) => t.safety_group === filter);
  }, [readyTests, filter]);

  const completedCount = useMemo(() => {
    return readyTests.filter((t) => attempts.some((a) => a.test_id === t.id)).length;
  }, [readyTests, attempts]);

  const avgPercent = useMemo(() => {
    const percents = readyTests
      .map((t) => bestPercentForTest(attempts, t.id))
      .filter((p) => p > 0);
    if (!percents.length) return 0;
    return Math.round(percents.reduce((a, b) => a + b, 0) / percents.length);
  }, [readyTests, attempts]);

  const chips = [{ id: "all", label: "Все темы" }, ...SAFETY_GROUPS.map((g) => ({ id: g.id, label: g.label }))];

  return (
    <TopNavLayout active="training">
      <header className="mockup-page-header">
        <h1>Тренировочные тесты</h1>
        <p>Выберите тему и начните тренировку для подготовки к экзамену</p>
      </header>

      <div className="training-layout">
        <div>
          <div className="training-filters">
            {chips.map((chip) => (
              <button
                key={chip.id}
                type="button"
                className={`training-chip${filter === chip.id ? " training-chip--active" : ""}`}
                onClick={() => setFilter(chip.id)}
              >
                {chip.label}
              </button>
            ))}
          </div>

          {error && <p className="auth-error">{error}</p>}
          {loading && <p className="mockup-page-header p">Загрузка…</p>}

          <div className="training-list">
            {filtered.map((t) => {
              const percent = bestPercentForTest(attempts, t.id);
              return (
                <div key={t.id} className="training-row">
                  <div>
                    <div className="training-row__category">{safetyGroupLabel(t.safety_group)}</div>
                    <div className="training-row__title">{t.title}</div>
                  </div>
                  <div className="training-row__meta">{t.ticket_count} билетов</div>
                  <div className="training-row__progress-wrap">
                    <div className="training-row__percent">{percent}%</div>
                    <div className="training-progress">
                      <div className="training-progress__bar" style={{ width: `${percent}%` }} />
                    </div>
                  </div>
                  <Link to={`/training/${t.id}`} className="mockup-link">
                    Начать
                  </Link>
                </div>
              );
            })}
            {!loading && !filtered.length && (
              <p className="mockup-page-header p">Нет доступных тренировочных тестов.</p>
            )}
          </div>
        </div>

        <aside className="training-sidebar">
          <div className="training-info-card">
            <svg className="training-info-card__icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
            <h3>Зачем тренироваться?</h3>
            <p>
              Регулярная практика помогает закрепить знания и уверенно пройти основной экзамен.
            </p>
          </div>
          <div className="training-progress-card">
            <h3>Ваш прогресс</h3>
            <div className="training-progress-card__stat">
              {completedCount} из {readyTests.length || "—"} тем пройдено
            </div>
            <div className="training-progress-card__avg">Средний результат: {avgPercent}%</div>
            <div className="training-progress">
              <div className="training-progress__bar" style={{ width: `${avgPercent}%` }} />
            </div>
          </div>
        </aside>
      </div>
    </TopNavLayout>
  );
}
