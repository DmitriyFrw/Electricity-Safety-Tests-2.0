import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import DashboardLayout from "../layout/DashboardLayout";
import { useGetReact } from "../hooks/useGetReact";
import type { Dashboard } from "../types/api";
import { formatDateRu, parseNextCheck } from "../utils/format";

export default function CabinetPage() {
  const { data, error, loading, reload } = useGetReact<Dashboard>("/dashboard");
  const [profileError, setProfileError] = useState("");
  const [profileSaved, setProfileSaved] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);

  if (error) return <DashboardLayout active="home"><p className="auth-error">{error}</p></DashboardLayout>;
  if (loading || !data) return <DashboardLayout active="home"><p className="dash-card-note">Загрузка…</p></DashboardLayout>;

  const examHref = data.exam_test_id ? `/exam/${data.exam_test_id}` : "/exam";
  const next = parseNextCheck(data.next_check_date);
  const isKot = data.user.role === "kot";

  const onProfileSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setProfileError("");
    setProfileSaved("");
    setSavingProfile(true);
    const fd = new FormData(e.target as HTMLFormElement);
    try {
      await api.updateProfile({
        full_name: String(fd.get("full_name")),
        birth_date: String(fd.get("birth_date")),
        job_title: String(fd.get("job_title")),
      });
      setProfileSaved("Данные сохранены");
      await reload();
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : "Ошибка сохранения");
    } finally {
      setSavingProfile(false);
    }
  };

  return (
    <DashboardLayout active="home">
      <section className="dash-hero">
        <div className="dash-hero-left">
          <h1>Личный кабинет</h1>
          <p className="dash-hero-sub">платформа для подготовки и сдачи экзамена по электробезопасности</p>
          <p className="dash-card-note">Роль: {data.user.role_label}</p>
          <div className="dash-hero-alert">
            <span className="dash-info-icon">i</span>
            Экзамен сдаётся в присутствии ответственного лица
          </div>
        </div>
        <div className="dash-hero-helmet" aria-hidden="true">
          <div className="dash-helmet-icon">
            <span className="dash-helmet-ya">Я</span>
          </div>
        </div>
        <div className="dash-hero-exam">
          <Link to={examHref} className="dash-exam-btn">Сдать экзамен</Link>
          <p className="dash-exam-hint">
            <span className="dash-info-icon sm">i</span>
            для успешной сдачи необходимо не менее {data.min_pass_percent}% правильных ответов
          </p>
        </div>
      </section>

      {isKot && (
        <section className="dash-section">
          <h2 className="dash-section-title">Данные для протокола PDF</h2>
          <div className="dash-page-card dash-form">
            {profileError && <p className="auth-error">{profileError}</p>}
            {profileSaved && <p className="dash-card-note">{profileSaved}</p>}
            <form onSubmit={onProfileSubmit}>
              <label htmlFor="full_name">ФИО</label>
              <input
                id="full_name"
                name="full_name"
                required
                maxLength={200}
                defaultValue={data.user.full_name ?? ""}
              />
              <label htmlFor="birth_date">Дата рождения</label>
              <input
                id="birth_date"
                name="birth_date"
                type="date"
                required
                defaultValue={data.user.birth_date ?? ""}
              />
              <label htmlFor="job_title">Занимаемая должность</label>
              <input
                id="job_title"
                name="job_title"
                required
                maxLength={200}
                defaultValue={data.user.job_title ?? ""}
              />
              <div style={{ marginTop: "1rem", display: "flex", gap: "1rem", flexWrap: "wrap" }}>
                <button type="submit" className="dash-exam-btn" disabled={savingProfile} style={{ border: "none", cursor: "pointer" }}>
                  {savingProfile ? "Сохранение…" : "Сохранить"}
                </button>
                <a href={api.protocolPdfUrl()} className="dash-exam-btn" style={{ textDecoration: "none" }}>
                  Скачать протокол PDF
                </a>
              </div>
            </form>
          </div>
        </section>
      )}

      <section className="dash-grid">
        <article className="dash-card dash-card-wide">
          <h2 className="dash-card-label">Количество доступных билетов</h2>
          <p className="dash-stat-big">{data.tickets_count}</p>
          <p className="dash-card-note">Изучите материалы по каждому билету перед сдачей</p>
          {data.materials_updated && (
            <p className="dash-card-meta">
              последняя редакция {formatDateRu(data.materials_updated).split(",")[0]}
            </p>
          )}
          <Link to="/training" className="dash-card-link">Перейти к обучению →</Link>
        </article>
        <article className="dash-card">
          <h2 className="dash-card-label">Протокол проверки знаний PDF</h2>
          <div className="dash-pdf-icon">PDF</div>
          <p className="dash-card-note">
            {isKot
              ? "Заполните данные выше и скачайте протокол"
              : "Протоколы формируются для роли Кот"}
          </p>
          {isKot ? (
            <a href={api.protocolPdfUrl()} className="dash-card-link">Скачать протокол →</a>
          ) : (
            <Link to="/exam" className="dash-card-link">Каталог экзаменов</Link>
          )}
        </article>
        <article className="dash-card dash-card-group">
          <h2 className="dash-card-label">Текущая группа по ЭБ</h2>
          <div className="dash-group-badge">{data.user.safety_group}</div>
          <p className="dash-group-desc">{data.user.safety_group_desc}</p>
        </article>
        <article className="dash-card dash-card-calendar">
          <h2 className="dash-card-label">Следующая проверка знаний</h2>
          <div className="dash-calendar">
            <span className="dash-cal-day">{next.day}</span>
            <span className="dash-cal-month">{next.month}</span>
          </div>
          <p className="dash-card-meta">{next.weekday} {next.short}</p>
        </article>
        <article className="dash-card">
          <h2 className="dash-card-label">Последний экзамен</h2>
          {data.last_percent != null ? (
            <>
              <p className="dash-stat-big dash-stat-percent">{data.last_percent}%</p>
              <p className="dash-card-note">
                {data.last_test_title && `«${data.last_test_title}»`}
                {data.last_test_date && ` · ${formatDateRu(data.last_test_date)}`}
              </p>
              {data.last_grade && (
                <p className={`dash-grade-line ${data.last_grade_class}`}>оценка: {data.last_grade}</p>
              )}
            </>
          ) : (
            <>
              <p className="dash-stat-big dash-stat-muted">—</p>
              <Link to={examHref} className="dash-card-link">Сдать первый экзамен →</Link>
            </>
          )}
        </article>
        <article className="dash-card">
          <h2 className="dash-card-label">Количество ошибок</h2>
          {data.last_errors != null ? (
            <>
              <p className="dash-stat-big dash-stat-errors">{data.last_errors}</p>
              <p className="dash-card-meta">допустимо не более {data.max_errors_allowed}</p>
            </>
          ) : (
            <p className="dash-stat-big dash-stat-muted">—</p>
          )}
        </article>
      </section>

      {data.can_create_tests && data.created_tests.length > 0 && (
        <section className="dash-section">
          <h2 className="dash-section-title">Мои тесты</h2>
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
                {data.created_tests.map((t) => (
                  <tr key={t.id}>
                    <td>{t.title}</td>
                    <td>{t.ticket_count}</td>
                    <td>
                      <Link to={`/tests/${t.id}/edit`}>Редактировать</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="dash-card-meta">
            <Link to="/tests/new">+ Создать тест</Link>
          </p>
        </section>
      )}

      {data.can_create_tests && data.created_tests.length === 0 && (
        <section className="dash-section">
          <Link to="/tests/new" className="dash-card-link">+ Создать тест</Link>
        </section>
      )}

      {data.attempts.length > 0 && (
        <section className="dash-section">
          <h2 className="dash-section-title">История</h2>
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
                {data.attempts.map((a) => (
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
