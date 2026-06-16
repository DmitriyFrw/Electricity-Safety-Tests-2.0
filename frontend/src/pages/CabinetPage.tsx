import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { axiosErrorMessage } from "../api/getReact";
import ProfileChart from "../components/ProfileChart";
import TopNavLayout from "../layout/TopNavLayout";
import { useGetReact } from "../hooks/useGetReact";
import { safetyGroupLabel } from "../constants/safetyGroups";
import type { Dashboard, StaffProtocolExport } from "../types/api";
import { BUSINESS_UNITS } from "../constants/businessUnits";
import { formatDateRu } from "../utils/format";
import { isProfileFieldsComplete, profileMissingLabels } from "../utils/profile";
import { userInitials } from "../utils/userInitials";
import {
  attemptKind,
  buildChartPoints,
  computeProfileStats,
  daysUntil,
  formatDateShort,
} from "../utils/profileStats";

function PassedExamTile({ row }: { row: StaffProtocolExport }) {
  return (
    <li>
      <Link to={`/exam/${row.test_id}/result/${row.attempt_id}`} className="mockup-link">
        {row.examinee_full_name || "Экзаменуемый"} — {row.test_title} · {row.percent}%
      </Link>
    </li>
  );
}

const IconPencil = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
    <path d="M12 20h9M16.5 3.5a2.12 2.12 0 013 3L7 19l-4 1 1-4 12.5-12.5z" />
  </svg>
);

const IconBolt = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
    <path d="M13 2L3 14h8l-1 8 10-12h-8l1-8z" />
  </svg>
);

const IconCalendar = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
    <rect x="3" y="5" width="18" height="16" rx="2" />
    <path d="M16 3v4M8 3v4M3 11h18" />
  </svg>
);

const IconDoc = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
    <path d="M14 2v6h6M8 13h8M8 17h5" />
  </svg>
);

const IconCheck = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
    <path d="M20 6L9 17l-5-5" />
  </svg>
);

const IconStar = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
    <path d="M12 2l2.9 6.1L21 9.3l-4.5 4.1L17.8 20 12 16.9 6.2 20l1.3-6.6L3 9.3l6.1-1.2L12 2z" />
  </svg>
);

const IconTrend = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
    <path d="M3 17l6-6 4 4 7-7" />
    <path d="M14 8h6v6" />
  </svg>
);

const IconBulb = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
    <path d="M9 18h6M10 22h4M8 14a6 6 0 1110.5-4.1A4.5 4.5 0 0114 14" />
  </svg>
);

export default function CabinetPage() {
  const { data, setData, error, loading, reload } = useGetReact<Dashboard>("/dashboard");
  const [profileError, setProfileError] = useState("");
  const [profileSaved, setProfileSaved] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [downloadingProtocol, setDownloadingProtocol] = useState(false);
  const [businessUnit, setBusinessUnit] = useState("");
  const [selectedAdminDraftUserId, setSelectedAdminDraftUserId] = useState<number | "">("");
  const [editOpen, setEditOpen] = useState(false);

  useEffect(() => {
    setBusinessUnit(data?.user.business_unit ?? "");
  }, [data?.user.business_unit, data?.user?.id]);

  useEffect(() => {
    const drafts = data?.admin_protocol_drafts;
    if (!drafts?.length) {
      setSelectedAdminDraftUserId("");
      return;
    }
    setSelectedAdminDraftUserId((prev) =>
      prev !== "" && drafts.some((u) => u.user_id === prev) ? prev : drafts[0].user_id
    );
  }, [data?.admin_protocol_drafts]);

  if (error) {
    return (
      <TopNavLayout>
        <p className="auth-error">{error}</p>
      </TopNavLayout>
    );
  }
  if (loading || !data) {
    return (
      <TopNavLayout>
        <p className="dash-card-note">Загрузка…</p>
      </TopNavLayout>
    );
  }

  const isKot = data.user.role === "kot";
  const isAdmin = data.user.role === "admin";
  const canExportStaffProtocol = data.can_create_tests;
  const staffExports = data.staff_protocol_exports ?? [];
  const adminDrafts = data.admin_protocol_drafts ?? [];
  const attempts = data.attempts ?? [];
  const stats = computeProfileStats(attempts, data.attempts_total, data.min_pass_percent);
  const chartPoints = buildChartPoints(attempts);
  const history = attempts.slice(0, 5);
  const daysLeft = daysUntil(data.next_check_date);
  const lastExamDate = data.last_passed_exam_date ?? data.last_test_date;
  const lastExamTitle = data.last_test_title ?? "Тестирование";
  const lastExamPercent = data.last_passed_exam_percent ?? data.last_percent;
  const lastPassedAttempt =
    attempts.find(
      (a) =>
        data.last_passed_exam_percent != null &&
        a.percent === data.last_passed_exam_percent &&
        (!data.last_passed_exam_date ||
          formatDateShort(a.finished_at) === formatDateShort(data.last_passed_exam_date))
    ) ?? attempts[0];
  const lastExamHref = lastPassedAttempt
    ? `/exam/${lastPassedAttempt.test_id}/result/${lastPassedAttempt.attempt_id}`
    : "/results";
  const profileUser = {
    ...data.user,
    business_unit: businessUnit.trim() || data.user.business_unit,
  };
  const profileReady =
    data.user.profile_complete === true || isProfileFieldsComplete(profileUser);
  const missingProfile = profileMissingLabels(profileUser);
  const businessUnitSaved = Boolean(data.user.business_unit?.trim());
  const displayName = data.user.full_name?.trim() || data.user.display_name || data.user.username;
  const initials = userInitials(data.user);

  const onProfileSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setProfileError("");
    setProfileSaved("");
    setSavingProfile(true);
    const fd = new FormData(e.target as HTMLFormElement);
    const full_name = String(fd.get("full_name") ?? "").trim();
    const birth_date = String(fd.get("birth_date") ?? "").trim();
    const job_title = String(fd.get("job_title") ?? "").trim();
    const business_unit = String(fd.get("business_unit") ?? "").trim();
    if (!full_name || !birth_date || !job_title || !business_unit) {
      setProfileError("Заполните ФИО, дату рождения, должность и юридическое лицо");
      setSavingProfile(false);
      return;
    }
    try {
      const updated = await api.updateProfile({ full_name, birth_date, job_title, business_unit });
      setBusinessUnit(updated.business_unit ?? business_unit);
      setData((prev) => (prev ? { ...prev, user: { ...prev.user, ...updated } } : prev));
      setProfileSaved("Данные сохранены");
      await reload();
    } catch (err) {
      setProfileError(axiosErrorMessage(err));
    } finally {
      setSavingProfile(false);
    }
  };

  const downloadProtocolDraft = async () => {
    setProfileError("");
    if (!isProfileFieldsComplete(profileUser)) {
      const missing = profileMissingLabels(profileUser);
      setProfileError(
        missing.length
          ? `Заполните профиль. Не заполнено: ${missing.join(", ")}.`
          : "Заполните профиль перед выгрузкой протокола."
      );
      return;
    }
    if (!businessUnitSaved) {
      setProfileError("Выберите бизнес-юнит и нажмите «Сохранить» перед скачиванием протокола.");
      return;
    }
    setDownloadingProtocol(true);
    try {
      const res = await fetch(api.profileProtocolPdfUrl(), { credentials: "include" });
      if (!res.ok) {
        let detail = "Не удалось скачать протокол";
        try {
          const body = (await res.json()) as { detail?: string };
          if (typeof body.detail === "string") detail = body.detail;
        } catch {
          /* ignore */
        }
        setProfileError(detail);
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "protocol.pdf";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setProfileError("Не удалось скачать протокол");
    } finally {
      setDownloadingProtocol(false);
    }
  };

  return (
    <TopNavLayout>
      <div className="profile-page">
        <header className="profile-page__header">
          <h1>Мой профиль</h1>
          <p>Здесь ваша личная статистика и информация о тестированиях</p>
        </header>

        <div className="profile-summary">
          <article className="profile-card profile-card--identity">
            <div className="profile-card__identity-row">
              <span className="profile-card__avatar">{initials}</span>
              <div>
                <h2 className="profile-card__name">{displayName}</h2>
                <p className="profile-card__meta">{data.user.username}</p>
                {data.user.business_unit && (
                  <p className="profile-card__meta">{data.user.business_unit}</p>
                )}
                {data.user.job_title && <p className="profile-card__meta">{data.user.job_title}</p>}
                {!data.user.job_title && (
                  <p className="profile-card__meta">{data.user.role_label}</p>
                )}
              </div>
            </div>
            {(isKot || !profileReady) && (
              <button
                type="button"
                className="profile-card__edit"
                onClick={() => setEditOpen((v) => !v)}
              >
                <IconPencil />
                {editOpen ? "Скрыть форму" : "Редактировать профиль"}
              </button>
            )}
          </article>

          <article className="profile-card profile-card--metric">
            <p className="profile-card__label">Группа электробезопасности</p>
            <div className="profile-card__metric-head">
              <span className="profile-card__icon profile-card__icon--yellow">
                <IconBolt />
              </span>
              <div className="profile-card__metric-text">
                <p className="profile-card__value">
                  {data.user.safety_group
                    ? safetyGroupLabel(data.user.safety_group)
                    : "—"}
                </p>
              </div>
            </div>
          </article>

          <article className="profile-card profile-card--metric">
            <p className="profile-card__label">Дата последнего тестирования</p>
            <div className="profile-card__metric-head">
              <span className="profile-card__icon profile-card__icon--purple">
                <IconCalendar />
              </span>
              <div className="profile-card__metric-text">
                <p className="profile-card__value">{formatDateShort(lastExamDate)}</p>
                <p className="profile-card__hint">{lastExamTitle}</p>
              </div>
            </div>
            {lastExamPercent != null && (
              <Link to={lastExamHref} className="profile-card__link mockup-link">
                Смотреть результат →
              </Link>
            )}
          </article>

          <article className="profile-card profile-card--metric">
            <p className="profile-card__label">Дата следующего тестирования</p>
            <div className="profile-card__metric-head">
              <span className="profile-card__icon profile-card__icon--yellow">
                <IconCalendar />
              </span>
              <div className="profile-card__metric-text">
                <p className="profile-card__value">{formatDateShort(data.next_check_date)}</p>
                <p className="profile-card__hint">Осталось {daysLeft} дней</p>
              </div>
            </div>
          </article>
        </div>

        {editOpen && isKot && (
          <section className="profile-edit-panel">
            <h2>Редактирование профиля</h2>
            {profileError && <p className="auth-error">{profileError}</p>}
            {profileSaved && <p className="dash-card-note">{profileSaved}</p>}
            {!profileReady && missingProfile.length > 0 && (
              <p className="dash-card-note">Не заполнено: {missingProfile.join(", ")}.</p>
            )}
            <form onSubmit={onProfileSubmit} className="dash-form">
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
              <div className="dash-form-row">
                <div className="dash-form-field">
                  <label htmlFor="job_title">Занимаемая должность</label>
                  <input
                    id="job_title"
                    name="job_title"
                    required
                    maxLength={200}
                    defaultValue={data.user.job_title ?? ""}
                  />
                </div>
                <div className="dash-form-field">
                  <label htmlFor="business_unit">Бизнес-юнит</label>
                  <select
                    id="business_unit"
                    name="business_unit"
                    required
                    value={businessUnit}
                    onChange={(e) => setBusinessUnit(e.target.value)}
                  >
                    <option value="" disabled>
                      Выберите ДЦ
                    </option>
                    {BUSINESS_UNITS.map((unit) => (
                      <option key={unit} value={unit}>
                        {unit}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div style={{ marginTop: "var(--spacing-4)", display: "flex", gap: "12px", flexWrap: "wrap" }}>
                <button type="submit" className="mockup-btn mockup-btn--primary" disabled={savingProfile}>
                  {savingProfile ? "Сохранение…" : "Сохранить"}
                </button>
                <button
                  type="button"
                  className="mockup-btn mockup-btn--outline"
                  disabled={downloadingProtocol}
                  onClick={() => void downloadProtocolDraft()}
                >
                  {downloadingProtocol ? "Формирование…" : "Скачать черновик протокола"}
                </button>
              </div>
            </form>
          </section>
        )}

        <div className="profile-layout">
          <div className="profile-layout__main">
            <section className="profile-panel">
              <h2 className="profile-panel__title">Общая статистика</h2>
              <div className="profile-stats-grid">
                <div className="profile-stat">
                  <span className="profile-stat__icon profile-stat__icon--purple">
                    <IconDoc />
                  </span>
                  <div className="profile-stat__text">
                    <p className="profile-stat__label">Пройдено тестов</p>
                    <p className="profile-stat__value">{stats.testsPassed}</p>
                  </div>
                </div>
                <div className="profile-stat">
                  <span className="profile-stat__icon profile-stat__icon--yellow">
                    <IconCheck />
                  </span>
                  <div className="profile-stat__text">
                    <p className="profile-stat__label">Средний результат</p>
                    <p className="profile-stat__value">{stats.averagePercent}%</p>
                  </div>
                </div>
                <div className="profile-stat">
                  <span className="profile-stat__icon profile-stat__icon--purple">
                    <IconStar />
                  </span>
                  <div className="profile-stat__text">
                    <p className="profile-stat__label">Лучший результат</p>
                    <p className="profile-stat__value">{stats.bestPercent}%</p>
                  </div>
                </div>
                <div className="profile-stat">
                  <span className="profile-stat__icon profile-stat__icon--yellow">
                    <IconTrend />
                  </span>
                  <div className="profile-stat__text">
                    <p className="profile-stat__label">Текущая серия</p>
                    <p className="profile-stat__value">{stats.currentStreak} тестов</p>
                  </div>
                </div>
              </div>

              <div className="profile-chart">
                <div className="profile-chart__head">
                  <h3 className="profile-panel__title">Динамика результатов</h3>
                  <select className="profile-chart__select" defaultValue="6" aria-label="Период графика">
                    <option value="6">За 6 месяцев</option>
                  </select>
                </div>
                <ProfileChart points={chartPoints} />
              </div>
            </section>
          </div>

          <div className="profile-layout__side">
            <section className="profile-panel">
              <div className="profile-panel__head">
                <h2 className="profile-panel__title">История тестирований</h2>
                <Link to="/results" className="mockup-link">
                  Все результаты →
                </Link>
              </div>
              {history.length === 0 ? (
                <p className="dash-card-note">Пока нет завершённых попыток.</p>
              ) : (
                <ul className="profile-history">
                  {history.map((a) => {
                    const kind = attemptKind(a, data.min_pass_percent);
                    const href =
                      kind === "exam"
                        ? `/exam/${a.test_id}/result/${a.attempt_id}`
                        : `/training/${a.test_id}/result/${a.attempt_id}`;
                    return (
                      <li key={a.attempt_id} className="profile-history__item">
                        <span
                          className={`profile-history__icon ${
                            kind === "exam" ? "profile-history__icon--ok" : "profile-history__icon--doc"
                          }`}
                        >
                          {kind === "exam" ? <IconCheck /> : <IconDoc />}
                        </span>
                        <div className="profile-history__body">
                          <p className="profile-history__title">
                            {kind === "exam" ? "Основной экзамен" : "Тренировочный тест"}
                          </p>
                          <p className="profile-history__meta">
                            {formatDateShort(a.finished_at)} · {a.test_title}
                          </p>
                        </div>
                        <Link to={href} className="profile-history__score">
                          {a.percent}% / {a.correct} из {a.total}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>

            <section className="profile-panel" style={{ marginTop: 20 }}>
              <h2 className="profile-panel__title">Рекомендации для вас</h2>
              <div className="profile-recommend">
                <p className="profile-recommend__text">
                  <span className="profile-recommend__bulb">
                    <IconBulb />
                  </span>
                  Рекомендуем пройти тренировочные тесты по темам, в которых ваши результаты ниже
                  среднего.
                </p>
                <Link to="/training" className="mockup-btn mockup-btn--primary mockup-btn--lg">
                  К тренировочным тестам →
                </Link>
              </div>
            </section>
          </div>
        </div>

        {(data.signed_protocol || isKot || isAdmin || canExportStaffProtocol) && (
          <section className="profile-panel profile-docs">
            <h2 className="profile-panel__title">Документы и протоколы</h2>

            {data.signed_protocol && (
              <div>
                <p className="dash-card-note">
                  Подписанный протокол: <strong>{data.signed_protocol.test_title}</strong> —{" "}
                  {data.signed_protocol.result_percent}% ({formatDateRu(data.signed_protocol.signed_at)})
                </p>
                <a
                  className="mockup-btn mockup-btn--outline"
                  href={api.signedProtocolPdfUrl(
                    data.signed_protocol.test_id,
                    data.signed_protocol.attempt_id
                  )}
                >
                  Скачать подписанный протокол (.pdf)
                </a>
              </div>
            )}

            {isKot && !editOpen && (
              <button
                type="button"
                className="mockup-btn mockup-btn--outline"
                disabled={downloadingProtocol}
                onClick={() => void downloadProtocolDraft()}
              >
                {downloadingProtocol ? "Формирование…" : "Скачать черновик протокола"}
              </button>
            )}

            {isAdmin && adminDrafts.length > 0 && (
              <div className="dash-protocol-draft-picker">
                <select
                  value={selectedAdminDraftUserId}
                  onChange={(e) => setSelectedAdminDraftUserId(Number(e.target.value))}
                  aria-label="Пользователь для черновика протокола"
                >
                  {adminDrafts.map((u) => (
                    <option key={u.user_id} value={u.user_id}>
                      {u.display_name} ({u.username})
                    </option>
                  ))}
                </select>
                {selectedAdminDraftUserId !== "" && (
                  <a
                    className="mockup-btn mockup-btn--outline"
                    href={api.adminUserProtocolDraftPdfUrl(selectedAdminDraftUserId)}
                  >
                    Черновик PDF
                  </a>
                )}
              </div>
            )}

            {canExportStaffProtocol && staffExports.length > 0 && (
              <ul>
                {staffExports.map((row) => (
                  <PassedExamTile key={row.attempt_id} row={row} />
                ))}
              </ul>
            )}
          </section>
        )}
      </div>
    </TopNavLayout>
  );
}
