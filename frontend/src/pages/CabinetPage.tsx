import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { axiosErrorMessage } from "../api/getReact";
import DashboardLayout from "../layout/DashboardLayout";
import { useGetReact } from "../hooks/useGetReact";
import { safetyGroupLabel } from "../constants/safetyGroups";
import type { Dashboard, StaffProtocolExport } from "../types/api";
import { BUSINESS_UNITS } from "../constants/businessUnits";
import { formatDateRu, parseNextCheck } from "../utils/format";
import { isProfileFieldsComplete, profileMissingLabels } from "../utils/profile";

function PassedExamTile({ row }: { row: StaffProtocolExport }) {
  return (
    <li className="dash-exam-export-item">
      <Link
        to={`/exam/${row.test_id}/result/${row.attempt_id}`}
        className="dash-exam-export-tile"
      >
        <strong>{row.examinee_full_name || "Экзаменуемый"}</strong>
        <div className="dash-card-meta">
          {row.test_title} · <span className="dash-exam-result-percent">{row.percent}%</span>
          {!row.profile_complete && (
            <>
              {" "}
              · <span className="grade-bad">профиль не заполнен</span>
            </>
          )}
        </div>
      </Link>
    </li>
  );
}

const InfoIcon = () => (
  <svg className="info-box-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
    <path
      fillRule="evenodd"
      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
      clipRule="evenodd"
    />
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
      <DashboardLayout active="home">
        <p className="auth-error">{error}</p>
      </DashboardLayout>
    );
  }
  if (loading || !data) {
    return (
      <DashboardLayout active="home">
        <p className="dash-card-note">Загрузка…</p>
      </DashboardLayout>
    );
  }

  const examHref = data.exam_test_id ? `/exam/${data.exam_test_id}` : "/exam";
  const next = parseNextCheck(data.next_check_date);
  const isKot = data.user.role === "kot";
  const isAdmin = data.user.role === "admin";
  const canExportStaffProtocol = data.can_create_tests;
  const staffExports = data.staff_protocol_exports ?? [];
  const adminDrafts = data.admin_protocol_drafts ?? [];
  const profileUser = {
    ...data.user,
    business_unit: businessUnit.trim() || data.user.business_unit,
  };
  const profileReady =
    data.user.profile_complete === true || isProfileFieldsComplete(profileUser);
  const missingProfile = profileMissingLabels(profileUser);
  const businessUnitSaved = Boolean(data.user.business_unit?.trim());
  const mascot = "/razvivaisia/assets/images/hedgehog-helmet.svg";

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
    <DashboardLayout active="home">
      <div className="dashboard-hero-row">
        <div className="dashboard-hero dashboard-hero-card">
          <div className="dashboard-hero-content">
            <h1>Личный кабинет</h1>
            <p>платформы для подготовки и сдачи экзамена по электробезопасности</p>
            <p className="dash-card-note">Роль: {data.user.role_label}</p>
          </div>
          <img src={mascot} alt="" className="dashboard-hero-mascot" />
        </div>

        <div className="dashboard-hero dashboard-hero-card dashboard-portal-intro">
          <h2 className="dashboard-portal-intro-title">Знакомство с порталом</h2>
          <p className="dashboard-portal-intro-desc">
            Тут вы найдете описание что и как тут работает
          </p>
          <Link to="/wiki" className="btn dashboard-portal-wiki-btn">
            Вики
          </Link>
        </div>
      </div>

      {isKot && (
        <div className="dashboard-widget" style={{ marginBottom: "var(--spacing-6)" }}>
          <div className="dashboard-widget-title">Данные для протокола PDF</div>
          {profileError && <p className="auth-error">{profileError}</p>}
          {profileSaved && <p className="dash-card-note">{profileSaved}</p>}
          {!profileReady && (
            <div className="info-box info-box-default" style={{ marginBottom: "var(--spacing-3)" }}>
              <InfoIcon />
              <span>
                Для выгрузки протокола заполните все поля, выберите бизнес-юнит и нажмите «Сохранить».
                {missingProfile.length > 0 && (
                  <> Не заполнено: {missingProfile.join(", ")}.</>
                )}
              </span>
            </div>
          )}
          <form onSubmit={onProfileSubmit} className="dash-form">
            <label htmlFor="full_name">ФИО</label>
            <input id="full_name" name="full_name" required maxLength={200} defaultValue={data.user.full_name ?? ""} />
            <label htmlFor="birth_date">Дата рождения</label>
            <input id="birth_date" name="birth_date" type="date" required defaultValue={data.user.birth_date ?? ""} />
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
            <div style={{ marginTop: "var(--spacing-4)", display: "flex", gap: "var(--spacing-3)", flexWrap: "wrap" }}>
              <button type="submit" className="btn btn-primary" disabled={savingProfile}>
                {savingProfile ? "Сохранение…" : "Сохранить"}
              </button>
              <button
                type="button"
                className="btn btn-outline"
                disabled={downloadingProtocol}
                title={
                  profileReady
                    ? undefined
                    : "Сначала сохраните профиль с бизнес-юнитом"
                }
                onClick={() => void downloadProtocolDraft()}
              >
                {downloadingProtocol ? "Формирование…" : "Скачать черновик протокола"}
              </button>
            </div>
          </form>
        </div>
      )}

      {data.signed_protocol && (
        <div className="dashboard-widget" style={{ marginBottom: "var(--spacing-6)" }}>
          <div className="dashboard-widget-title">Подписанный протокол экзамена</div>
          <p className="dash-card-note">
            Экзамен: <strong>{data.signed_protocol.test_title}</strong>
            <br />
            Результат: <strong>{data.signed_protocol.result_percent}%</strong>
            <br />
            Подписал: <strong>{data.signed_protocol.signer_username}</strong>
            <br />
            Дата подписи: {formatDateRu(data.signed_protocol.signed_at)}
          </p>
          <a
            className="btn btn-outline"
            href={api.signedProtocolPdfUrl(
              data.signed_protocol.test_id,
              data.signed_protocol.attempt_id
            )}
          >
            Скачать подписанный протокол (.pdf)
          </a>
        </div>
      )}

      <div className="dashboard-stats">
        <div className="dashboard-widget widget-tickets">
          <div className="dashboard-widget-header">
            <div>
              <div className="dashboard-widget-title">Количество доступных билетов</div>
              <div className="dashboard-widget-subtitle">
                для изучения материалов необходимых для успешной сдачи экзамена по электробезопасности
              </div>
            </div>
          </div>
          <div className="dashboard-widget-value">{data.tickets_count}</div>
          {data.materials_updated && (
            <div className="dashboard-widget-footer">
              последняя редакция {formatDateRu(data.materials_updated).split(",")[0]}
            </div>
          )}
          <Link to="/training" className="dash-card-link" style={{ display: "inline-block", marginTop: "var(--spacing-3)" }}>
            Перейти к обучению →
          </Link>
        </div>

        <div className="dashboard-widget widget-protocol">
          <div className="dashboard-widget-header">
            <div className="dashboard-widget-title">Черновик протокола (PDF)</div>
          </div>
          {isKot ? (
            <button
              type="button"
              className="btn btn-outline"
              disabled={downloadingProtocol}
              onClick={() => void downloadProtocolDraft()}
            >
              {downloadingProtocol ? "Формирование…" : "Скачать черновик"}
            </button>
          ) : isAdmin ? (
            <>
              {adminDrafts.length > 0 ? (
                <>
                  <p className="dash-card-note" style={{ marginBottom: "var(--spacing-2)" }}>
                    Черновик из профиля пользователя (без сдачи экзамена):
                  </p>
                  <div className="dash-protocol-draft-picker">
                    <select
                      id="admin-protocol-draft-user"
                      className="dash-protocol-draft-select"
                      value={selectedAdminDraftUserId}
                      onChange={(e) => setSelectedAdminDraftUserId(Number(e.target.value))}
                      aria-label="Выбор пользователя для черновика протокола"
                    >
                      {adminDrafts.map((u) => (
                        <option key={u.user_id} value={u.user_id}>
                          {u.display_name} ({u.username})
                        </option>
                      ))}
                    </select>
                    {selectedAdminDraftUserId !== "" && (
                      <a
                        className="btn btn-outline btn-sm"
                        href={api.adminUserProtocolDraftPdfUrl(selectedAdminDraftUserId)}
                        style={{ textDecoration: "none", flexShrink: 0 }}
                      >
                        Черновик PDF
                      </a>
                    )}
                  </div>
                </>
              ) : (
                <p className="dash-card-note">
                  Нет пользователей с заполненным профилем.{" "}
                  <Link to="/admin/users" className="dash-card-link">
                    Открыть «Пользователи»
                  </Link>
                </p>
              )}
              {staffExports.length > 0 && (
                <>
                  <p
                    className="dash-card-note"
                    style={{ marginTop: "var(--spacing-4)", marginBottom: "var(--spacing-2)" }}
                  >
                    После сданных экзаменов:
                  </p>
                  <ul className="constructor-drafts-list" style={{ marginTop: 0 }}>
                    {staffExports.map((row) => (
                      <PassedExamTile key={row.attempt_id} row={row} />
                    ))}
                  </ul>
                </>
              )}
            </>
          ) : canExportStaffProtocol ? (
            staffExports.length > 0 ? (
              <ul className="constructor-drafts-list" style={{ marginTop: 0 }}>
                {staffExports.map((row) => (
                  <PassedExamTile key={row.attempt_id} row={row} />
                ))}
              </ul>
            ) : (
              <p className="dash-card-note">
                Пока нет успешно сданных экзаменов. После сдачи здесь появятся ссылки на выгрузку
                протокола.
              </p>
            )
          ) : (
            <span className="dash-card-note">Доступно для роли Кот</span>
          )}
          <div className="info-box info-box-default" style={{ marginTop: "var(--spacing-4)" }}>
            <InfoIcon />
            <span>
              {isKot
                ? "Черновик из данных профиля. После сдачи экзамена подписанный протокол появится в блоке выше или на странице результата."
                : isAdmin
                  ? "Администратор может скачать черновик по любому пользователю с заполненным профилем. Результат сданного экзамена открывается по клику на карточку."
                  : canExportStaffProtocol
                    ? "Нажмите на карточку результата, чтобы открыть страницу экзамена с разбором ответов."
                    : "Черновик из данных профиля."}
            </span>
          </div>
        </div>

        <div className="dashboard-widget widget-group">
          <div className="dashboard-widget-title">Текущая группа по ЭБ</div>
          <div className="dashboard-widget-value">{safetyGroupLabel(data.user.safety_group)}</div>
          {data.last_passed_exam_percent != null && data.last_passed_exam_date && (
            <div className="dashboard-widget-footer widget-group-passed">
              сдача {formatDateRu(data.last_passed_exam_date).split(",")[0]} ·{" "}
              {data.last_passed_exam_percent}%
              {data.last_passed_exam_grade ? ` · ${data.last_passed_exam_grade}` : ""}
            </div>
          )}
        </div>
      </div>

      <div className="dashboard-bottom-stats">
        <div className="dashboard-widget widget-date">
          <div className="dashboard-widget-title">Следующая проверка знаний</div>
          <div className="dashboard-widget-subtitle">назначена на:</div>
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "center", gap: "var(--spacing-4)", margin: "var(--spacing-4) 0" }}>
            <div>
              <div className="widget-date-day">{next.day}</div>
              <div className="widget-date-month">{next.month}</div>
            </div>
            <div>
              <div className="widget-date-weekday">{next.weekday}</div>
              <div className="widget-date-full">{next.short}</div>
            </div>
          </div>
        </div>

        <div className="dashboard-widget">
          <div className="dashboard-widget-title">Последний экзамен</div>
          {data.last_percent != null ? (
            <div className="widget-result">
              <div className="widget-result-percentage">{data.last_percent}%</div>
              <div className="widget-result-details">
                {data.last_test_title && <div>«{data.last_test_title}»</div>}
                {data.last_test_date && <div>за тест от: {formatDateRu(data.last_test_date).split(",")[0]}</div>}
                {data.last_grade && (
                  <div className={data.last_grade_class ?? undefined}>оценка: {data.last_grade}</div>
                )}
              </div>
            </div>
          ) : (
            <Link to={examHref} className="dash-card-link">
              Сдать первый экзамен →
            </Link>
          )}
        </div>

        <div className="dashboard-widget">
          <div className="dashboard-widget-title">Количество ошибок</div>
          <div className="dashboard-widget-subtitle">за прошлый тест:</div>
          {data.last_errors != null ? (
            <div className="widget-errors">
              <div className="widget-errors-count">{data.last_errors}</div>
              <div className="widget-errors-details">
                <div className="widget-errors-allowed">
                  Допустимое количество ошибок не более <strong>{data.max_errors_allowed}</strong>
                </div>
              </div>
            </div>
          ) : (
            <div className="dashboard-widget-value">—</div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
