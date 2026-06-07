import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api } from "../api/client";
import { axiosErrorMessage } from "../api/getReact";
import { useAuth } from "../auth/AuthContext";
import TestResultTiles from "../components/test-flow/TestResultTiles";
import DashboardLayout from "../layout/DashboardLayout";
import type { ExamResult, SignedProtocol } from "../types/api";
import { formatDateRu } from "../utils/format";

type ExamResultViewProps = {
  testId: number;
  result: ExamResult;
};

function ExamResultView({ testId, result }: ExamResultViewProps) {
  const { user } = useAuth();
  const [protocol, setProtocol] = useState<SignedProtocol | null>(null);
  const [actionError, setActionError] = useState("");
  const [signing, setSigning] = useState(false);
  const [loadingProtocol, setLoadingProtocol] = useState(false);

  const attemptId = result.attempt_id;

  useEffect(() => {
    if (!result.protocol_signed) return;
    let cancelled = false;
    setLoadingProtocol(true);
    void api
      .getSignedProtocol(testId, attemptId)
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
  }, [result.protocol_signed, attemptId, testId]);

  const canSign = Boolean(
    result.passed_exam && (user?.role === "admin" || user?.role === "ezh")
  );
  const isSigned = result.protocol_signed || Boolean(protocol);
  const draftPdfUrl = api.attemptProtocolDraftPdfUrl(testId, attemptId);
  const formPdfUrl = api.attemptProtocolFormPdfUrl(testId, attemptId);
  const signedPdfUrl = api.signedProtocolPdfUrl(testId, attemptId);

  async function onSign() {
    setSigning(true);
    setActionError("");
    try {
      const signed = await api.signProtocol(testId, attemptId);
      setProtocol(signed);
    } catch (e) {
      setActionError(axiosErrorMessage(e));
    } finally {
      setSigning(false);
    }
  }

  async function onLoadProtocol() {
    setLoadingProtocol(true);
    setActionError("");
    try {
      const p = await api.getSignedProtocol(testId, attemptId);
      setProtocol(p);
    } catch (e) {
      setActionError(axiosErrorMessage(e));
    } finally {
      setLoadingProtocol(false);
    }
  }

  return (
    <DashboardLayout active="exam">
      <section className="dash-hero">
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
          {canSign && (
            <div
              className="constructor-page-actions"
              style={{ marginBottom: "var(--spacing-3)" }}
            >
              <a
                className="btn btn-outline"
                href={draftPdfUrl}
                style={{ textDecoration: "none" }}
              >
                Черновик из профиля (.pdf)
              </a>
              <a
                className="dash-exam-btn"
                href={formPdfUrl}
                style={{ textDecoration: "none" }}
              >
                Форма протокола (.pdf)
              </a>
              {!isSigned && (
                <button
                  type="button"
                  className="dash-exam-btn"
                  onClick={() => void onSign()}
                  disabled={signing}
                  style={{ border: "none", cursor: "pointer" }}
                >
                  {signing ? "Подписание…" : "Подписать"}
                </button>
              )}
            </div>
          )}
          {!isSigned && user?.role === "kot" && (
            <p className="dash-card-note">
              Протокол будет доступен для скачивания после подписи контролирующим лицом (Еж или
              Администратор).
            </p>
          )}
          {isSigned && (
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
              <a
                className="dash-exam-btn"
                href={signedPdfUrl}
                style={{ display: "inline-block", marginTop: "var(--spacing-3)" }}
              >
                Скачать подписанный протокол (.pdf)
              </a>
            </div>
          )}
          {!isSigned && user?.role === "kot" && (
            <button
              type="button"
              className="dash-card-link"
              onClick={() => void onLoadProtocol()}
              disabled={loadingProtocol}
              style={{
                border: "none",
                background: "transparent",
                cursor: "pointer",
                marginTop: "var(--spacing-2)",
              }}
            >
              {loadingProtocol ? "Проверка…" : "Обновить статус подписи"}
            </button>
          )}
          {actionError && <p className="auth-error">{actionError}</p>}
        </section>
      )}

      {(result.question_results?.length ?? 0) > 0 && (
        <TestResultTiles
          questions={result.question_results ?? []}
          reviewBasePath={`/exam/${testId}/result`}
          result={result}
        />
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

export default function ExamResultPage() {
  const { testId, attemptId } = useParams();
  const location = useLocation();
  const stateResult = location.state?.result as ExamResult | undefined;

  const tid = Number(testId);
  const aid = attemptId ? Number(attemptId) : null;
  const hasTestId = Number.isFinite(tid) && tid > 0;

  const [result, setResult] = useState<ExamResult | null>(stateResult ?? null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(!stateResult && aid != null && Number.isFinite(aid));

  useEffect(() => {
    if (stateResult) {
      setResult(stateResult);
      setLoading(false);
      return;
    }
    if (!hasTestId || aid == null || !Number.isFinite(aid)) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setLoadError("");
    void api
      .getExamResult(tid, aid)
      .then((data) => {
        if (!cancelled) setResult(data);
      })
      .catch((err) => {
        if (!cancelled) setLoadError(axiosErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [stateResult, hasTestId, tid, aid]);

  if (loading) {
    return (
      <DashboardLayout active="exam">
        <p className="dash-card-note">Загрузка…</p>
      </DashboardLayout>
    );
  }

  if (loadError) {
    return (
      <DashboardLayout active="exam">
        <p className="auth-error">{loadError}</p>
        <Link to="/cabinet">В кабинет</Link>
      </DashboardLayout>
    );
  }

  if (!result) {
    return (
      <DashboardLayout active="exam">
        <p className="dash-card-note">Нет данных результата.</p>
        <Link to={hasTestId ? `/exam/${tid}` : "/exam"}>Вернуться к экзамену</Link>
      </DashboardLayout>
    );
  }

  if (!hasTestId) {
    return (
      <DashboardLayout active="exam">
        <p className="dash-card-note">Некорректный идентификатор теста.</p>
        <Link to="/exam">Вернуться к экзамену</Link>
      </DashboardLayout>
    );
  }

  return <ExamResultView testId={tid} result={result} />;
}
