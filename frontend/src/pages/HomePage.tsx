import { Link } from "react-router-dom";
import TopNavLayout from "../layout/TopNavLayout";

const BookIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M4 19.5A2.5 2.5 0 016.5 17H20" />
    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" />
  </svg>
);

const CapIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M22 10l-10-5L2 10l10 5 10-5z" />
    <path d="M6 12v5c0 2 4 3 6 3s6-1 6-3v-5" />
  </svg>
);

const ChartIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M18 20V10M12 20V4M6 20v-6" />
  </svg>
);

export default function HomePage() {
  return (
    <TopNavLayout active="home">
      <section className="landing-hero">
        <div>
          <h1 className="landing-hero__title">
            Ежегодное тестирование — шаг к вашему <span className="landing-hero__accent">развитию</span>
          </h1>
          <p className="landing-hero__subtitle">
            Проходите тренировочные тесты, готовьтесь и сдавайте основной экзамен.
          </p>
          <div className="landing-hero__actions">
            <Link to="/training" className="mockup-btn mockup-btn--primary">
              Перейти к тренировкам
            </Link>
            <Link to="/exam" className="mockup-btn mockup-btn--outline">
              О экзамене
            </Link>
            <Link to="/wiki" className="mockup-btn mockup-btn--portal">
              О портале
            </Link>
          </div>
        </div>
        <div className="landing-hero__visual">
          <img
            src="/razvivaisia/assets/images/ezhkot-privet.png"
            alt="Ежекот"
            className="landing-hero__mascot"
            width={520}
            height={520}
          />
        </div>
      </section>

      <section className="landing-features">
        <article className="landing-feature">
          <div className="landing-feature__icon landing-feature__icon--yellow">
            <BookIcon />
          </div>
          <h3>Тренируйтесь</h3>
          <p>Практикуйтесь на примерах, чтобы чувствовать себя уверенно</p>
          <Link to="/training" className="mockup-link">
            К тренировкам →
          </Link>
        </article>
        <article className="landing-feature">
          <div className="landing-feature__icon landing-feature__icon--purple">
            <CapIcon />
          </div>
          <h3>Сдайте экзамен</h3>
          <p>Пройдите основной тест в отведённое время</p>
          <Link to="/exam" className="mockup-link">
            К экзамену →
          </Link>
        </article>
        <article className="landing-feature">
          <div className="landing-feature__icon landing-feature__icon--yellow">
            <ChartIcon />
          </div>
          <h3>Отслеживайте прогресс</h3>
          <p>Смотрите результаты и развивайтесь дальше</p>
          <Link to="/results" className="mockup-link">
            К результатам →
          </Link>
        </article>
      </section>
    </TopNavLayout>
  );
}
