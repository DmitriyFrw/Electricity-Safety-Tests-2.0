import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api } from "../api/client";
import { axiosErrorMessage } from "../api/getReact";
import { useAuth } from "../auth/AuthContext";
import DashboardLayout from "../layout/DashboardLayout";
import type { ExamResult, SignedProtocol } from "../types/api";
import { formatDateRu } from "../utils/format";

export default function ExamResultPage() {
  const { testId } = useParams();
  const location = useLocation();
  const { user } = useAuth();
  const result = location.state?.result as ExamResult | undefined;
  const [protocol, setProtocol] = useState<SignedProtocol | null>(null);
  const [actionError, setActionError] = useState("");
  const [signing, setSigning] = useState(false);
  const [loadingProtocol, setLoadingProtocol] = useState(false);

  const tid = Number(testId);
  const hasTestId = Number.isFinite(tid) && tid > 0;

  useEffect(() => {
    if (!result?.protocol_signed || !hasTestId) return;
    let cancelled = false;
    setLoadingProtocol(true);
    void api
      .getSignedProtocol(tid, result.attempt_id)
      .then((p) => {
        if (!cancelled) setProtocol(p);
      })
      .catch(() => {
        /* PDF доступен и без метаданных */
      })
      .finally(() => {
        if (!cancelled) setLoadingProtocol(false);
      });
    return () => {
      cancelled = true;
    };
  }, [result?.protocol_signed, result?.attempt_id, hasTestId, tid]);

  if (!result) {
    return (
      <DashboardLayout active="exam">
        <p className="dash-card-note">Нет данных результата.</p>
        <Link to={hasTestId ? `/exam/${tid}` : "/exam"}>Вернуться к экзамену</Link>
      </DashboardLayout>
    );
  }

  const canSign = Boolean(
    result.passed_exam && (user?.role === "admin" || user?.role === "ezh")
  );
  const isSigned = result.protocol_signed || Boolean(protocol);
  const pdfUrl = hasTestId ? api.signedProtocolPdfUrl(tid, result.attempt_id) : null;

  async function onSign() {
    if (!hasTestId) return;
    setSigning(true);
    setActionError("");
    try {
      const signed = await api.signProtocol(tid, result.attempt_id);
      setProtocol(signed);
    } catch (e) {
      setActionError(axiosErrorMessage(e));
    } finally {
      setSigning(false);
    }
  }

  async function onLoadProtocol() {
    if (!hasTestId) return;
    setLoadingProtocol(true);
    setActionError("");
    try {
      const p = await api.getSignedProtocol(tid, result.attempt_id);
      setProtocol(p);
    } catch (e) {
      setActionError(axiosErrorMessage(e));
    } finally {
      setLoadingProtocol(false);
    }
  }

  return (
    <DashboardLayout active="exam">
      <section className="dash-hero" style={{ gridTemplateColumns: "1fr auto" }}>
        <div>
          <h1>Результат экзамена</h1>
          <p className="dash-hero-sub">{result.test_title}</p>
          <p className="dash-stat-big dash-stat-percent">{result.percent}%</p>
          <p className={`dash-grade-line ${result.grade_class}`}>оценка: {result.grade}</p>
          <p className="dash-card-note">
            {result.correct} из {result.total} · ошибок: {result.errors} ·{" "}
            {result.passed_exam ? (
              <span className="grade-excellent">сдан</span>
            ) : (
              <span className="grade-bad">не сдан (нужно ≥ {result.min_pass_percent}%)</span>
            )}
          </p>
        </div>
        <Link to="/cabinet" className="dash-exam-btn">
          В кабинет
        </Link>
      </section>

      {result.passed_exam && (
        <section className="dash-page-card">
          <h2 className="dash-section-title" style={{ marginTop: 0 }}>
            Протокол экзамена
          </h2>
          {canSign && !isSigned && (
            <button
              type="button"
              className="dash-exam-btn"
              onClick={() => void onSign()}
              disabled={signing}
              style={{ border: "none", cursor: "pointer", marginBottom: "var(--spacing-3)" }}
            >
              {signing ? "Подписание…" : "Подписать"}
            </button>
          )}
          {result.passed_exam && !isSigned && user?.role === "kot" && (
            <p className="dash-card-note">
              Протокол будет доступен для скачивания после подписи контролирующим лицом (Еж или
              Администратор).
            </p>
          )}
          {isSigned && pdfUrl && (
            <div className="dash-card-note">
              {loadingProtocol && !protocol && <p>Загрузка данных протокола…</p>}
              {protocol && (
                <>
                  Подписал: <strong>{protocol.signer_username}</strong>
                  <br />
                  Экзаменуемый: <strong>{protocol.examinee_full_name}</strong>
                  <br />
                  Дата подписи: {formatDateRu(protocol.signed_at)}
                  <br />
                </>
              )}
              <a className="dash-exam-btn" href={pdfUrl} style={{ display: "inline-block", marginTop: "var(--spacing-3)" }}>
                Скачать подписанный протокол (.pdf)
              </a>
            </div>
          )}
          {!isSigned && result.passed_exam && user?.role === "kot" && (
            <button
              type="button"
              className="dash-card-link"
              onClick={() => void onLoadProtocol()}
              disabled={loadingProtocol}
              style={{ border: "none", background: "transparent", cursor: "pointer", marginTop: "var(--spacing-2)" }}
            >
              {loadingProtocol ? "Проверка…" : "Обновить статус подписи"}
            </button>
          )}
          {actionError && <p className="auth-error">{actionError}</p>}
        </section>
      )}

      {result.ticket_rows.length > 0 && (
        <div className="dash-table-wrap">
          <table className="dash-table">
            <thead>
              <tr>
                <th>Билет</th>
                <th>Правильно</th>
                <th>%</th>
                <th>Оценка</th>
              </tr>
            </thead>
            <tbody>
              {result.ticket_rows.map((r) => (
                <tr key={r.n}>
                  <td>№{r.n}</td>
                  <td>
                    {r.correct}/{r.total}
                  </td>
                  <td>{r.percent}%</td>
                  <td className={r.grade_class}>{r.grade}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </DashboardLayout>
  );
}
