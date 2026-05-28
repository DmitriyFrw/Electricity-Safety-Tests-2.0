import { useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { axiosErrorMessage, getReact, postReact } from "../api/getReact";
import { useAuth } from "../auth/AuthContext";
import DashboardLayout from "../layout/DashboardLayout";
import type { ExamResult, SignedProtocol } from "../types/api";

export default function ExamResultPage() {
  const { testId } = useParams();
  const location = useLocation();
  const { user } = useAuth();
  const result = location.state?.result as ExamResult | undefined;
  const [protocol, setProtocol] = useState<SignedProtocol | null>(null);
  const [actionError, setActionError] = useState("");
  const [signing, setSigning] = useState(false);

  if (!result) {
    return (
      <DashboardLayout active="exam">
        <p className="dash-card-note">Нет данных результата.</p>
        <Link to={`/exam/${testId}`}>Вернуться к экзамену</Link>
      </DashboardLayout>
    );
  }

  const canSign = Boolean(
    result.passed_exam && (user?.role === "admin" || user?.role === "ezh")
  );
  const isSigned = result.protocol_signed || Boolean(protocol);

  async function onSign() {
    if (!testId) return;
    setSigning(true);
    setActionError("");
    try {
      const signed = await postReact<SignedProtocol>(
        `/tests/${testId}/exam/attempts/${result.attempt_id}/protocol/sign`
      );
      setProtocol(signed);
    } catch (e) {
      setActionError(axiosErrorMessage(e));
    } finally {
      setSigning(false);
    }
  }

  async function onLoadProtocol() {
    if (!testId) return;
    setActionError("");
    try {
      const p = await getReact<SignedProtocol>(
        `/tests/${testId}/exam/attempts/${result.attempt_id}/protocol`
      );
      setProtocol(p);
    } catch (e) {
      setActionError(axiosErrorMessage(e));
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
      <section className="dash-page-card">
        {canSign && !isSigned && (
          <button
            type="button"
            className="dash-exam-btn"
            onClick={onSign}
            disabled={signing}
            style={{ border: "none", cursor: "pointer" }}
          >
            {signing ? "Подписание..." : "Подписать"}
          </button>
        )}
        {!protocol && (
          <button
            type="button"
            className="dash-card-link"
            onClick={onLoadProtocol}
            style={{ border: "none", background: "transparent", cursor: "pointer" }}
          >
            Проверить статус протокола
          </button>
        )}
        {protocol && (
          <div className="dash-card-note">
            Подписал: <strong>{protocol.signer_username}</strong>, экзаменуемый:{" "}
            <strong>{protocol.examinee_full_name}</strong>
            <br />
            <a
              className="dash-exam-btn"
              href={`/api/tests/${testId}/exam/attempts/${result.attempt_id}/protocol.pdf`}
            >
              Скачать .pdf
            </a>
          </div>
        )}
        {actionError && <p className="auth-error">{actionError}</p>}
      </section>
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
