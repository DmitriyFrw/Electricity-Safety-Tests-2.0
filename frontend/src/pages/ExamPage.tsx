import { Link } from "react-router-dom";
import TopNavLayout from "../layout/TopNavLayout";
import {
  examPassThresholdLabel,
  examQuestionsPerTicketLabel,
  examTicketTimeLabel,
} from "../content/examRules";
import { useGetReact } from "../hooks/useGetReact";
import type { TestListItem } from "../types/api";

const CheckIcon = () => (
  <svg className="exam-recommendations__check" viewBox="0 0 20 20" fill="currentColor">
    <path
      fillRule="evenodd"
      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
      clipRule="evenodd"
    />
  </svg>
);

const RECOMMENDATIONS = [
  "Не обновляйте страницу и не закрывайте вкладку",
  "Следите за временем",
  "Проверьте соединение с интернетом",
  "После завершения нажмите «Завершить экзамен»",
];

export default function ExamPage() {
  const { data, error, loading } = useGetReact<{ items: TestListItem[] }>("/tests");
  const tests = data?.items ?? [];
  const firstReady = tests.find((t) => t.ready);

  return (
    <TopNavLayout active="exam">
      <div className="exam-mockup">
        <div>
          <header className="mockup-page-header">
            <h1>Основной экзамен</h1>
            <p>Внимательно читайте вопросы и выбирайте правильные ответы. Удачи!</p>
          </header>

          <div className="exam-mockup__stats">
            <div className="exam-stat-card">
              <div className="exam-stat-card__icon exam-stat-card__icon--yellow">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 6v6l4 2" />
                </svg>
              </div>
              <div className="exam-stat-card__label">Время</div>
              <div className="exam-stat-card__value">{examTicketTimeLabel()}</div>
            </div>
            <div className="exam-stat-card">
              <div className="exam-stat-card__icon exam-stat-card__icon--purple">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z" />
                </svg>
              </div>
              <div className="exam-stat-card__label">Вопросов</div>
              <div className="exam-stat-card__value">{examQuestionsPerTicketLabel()}</div>
            </div>
            <div className="exam-stat-card">
              <div className="exam-stat-card__icon exam-stat-card__icon--yellow">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
              </div>
              <div className="exam-stat-card__label">Проходной балл</div>
              <div className="exam-stat-card__value">{examPassThresholdLabel()}</div>
            </div>
          </div>

          <section className="exam-recommendations">
            <h2>Рекомендации</h2>
            <ul>
              {RECOMMENDATIONS.map((text) => (
                <li key={text}>
                  <CheckIcon />
                  {text}
                </li>
              ))}
            </ul>
          </section>

          {error && <p className="auth-error">{error}</p>}
          {loading && <p>Загрузка…</p>}
          {!loading && !error && !firstReady && (
            <p>Нет доступных тестов для экзамена.</p>
          )}
        </div>

        <aside className="exam-mockup__aside">
          <div className="exam-mockup__visual">
            <img
              src="/razvivaisia/assets/images/ezhkot-laptop.png"
              alt="Ежекот за ноутбуком"
              className="exam-mockup__mascot"
              width={440}
              height={440}
            />
          </div>
          {firstReady && (
            <Link to={`/exam/${firstReady.id}`} className="mockup-btn mockup-btn--primary mockup-btn--lg">
              Начать экзамен
            </Link>
          )}
          <p className="exam-mockup__note">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z" />
            </svg>
            Ваши ответы сохраняются автоматически
          </p>
        </aside>
      </div>
    </TopNavLayout>
  );
}
