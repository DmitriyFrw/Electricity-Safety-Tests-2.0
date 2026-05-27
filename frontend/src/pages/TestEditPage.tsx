import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { deleteReact, postReact, putReact } from "../api/getReact";
import DashboardLayout from "../layout/DashboardLayout";
import { useGetReact } from "../hooks/useGetReact";
import type { QuestionSave, TestEdit } from "../types/api";

const CORRECT_OPTIONS = ["A", "B", "C", "D"];

function indexToLetter(index: number): string {
  return CORRECT_OPTIONS[index] ?? "A";
}

export default function TestEditPage() {
  const { testId } = useParams();
  const id = Number(testId);
  const editPath = id ? `/tests/${id}` : null;
  const { data: test, setData: setTest, error, loading } = useGetReact<TestEdit>(editPath, Boolean(id));
  const [actionError, setActionError] = useState("");
  const [saving, setSaving] = useState(false);

  const addTicket = async () => {
    if (!id) return;
    try {
      setTest(await postReact<TestEdit>(`/tests/${id}/tickets`));
      setActionError("");
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Ошибка");
    }
  };

  const deleteTicket = async (ticketId: number) => {
    if (!id || !confirm("Удалить билет?")) return;
    try {
      setTest(await deleteReact<TestEdit>(`/tests/${id}/tickets/${ticketId}`));
      setActionError("");
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Ошибка");
    }
  };

  const saveTicket = async (ticketId: number, e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!id || !test) return;
    setSaving(true);
    const fd = new FormData(e.currentTarget);
    const questions: QuestionSave[] = [];
    for (let pos = 1; pos <= test.questions_per_ticket; pos++) {
      questions.push({
        position: pos,
        text: String(fd.get(`q${pos}_text`) || ""),
        option_a: String(fd.get(`q${pos}_a`) || ""),
        option_b: String(fd.get(`q${pos}_b`) || ""),
        option_c: String(fd.get(`q${pos}_c`) || ""),
        option_d: String(fd.get(`q${pos}_d`) || ""),
        correct: String(fd.get(`q${pos}_correct`) || "A"),
      });
    }
    try {
      setTest(await putReact<TestEdit>(`/tests/${id}/tickets/${ticketId}`, { questions }));
      setActionError("");
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  };

  if (loading || !test) {
    return (
      <DashboardLayout active="home">
        <p className="dash-card-note">{error || "Загрузка…"}</p>
      </DashboardLayout>
    );
  }

  const displayError = actionError || error;

  return (
    <DashboardLayout active="home">
      <div className="dash-page-card">
        <h1>{test.title}</h1>
        <p className="dash-card-meta">
          Билетов {test.tickets.length}/{test.max_tickets}
          {test.ready ? " · готов к сдаче" : " · заполните все билеты"}
        </p>
        {displayError && <p className="auth-error">{displayError}</p>}
        <button
          type="button"
          className="dash-exam-btn"
          style={{ border: "none", cursor: "pointer" }}
          disabled={test.tickets.length >= test.max_tickets}
          onClick={() => void addTicket()}
        >
          Добавить билет
        </button>
        {test.ready && (
          <Link to={`/exam/${test.id}`} className="dash-exam-btn" style={{ marginLeft: "0.5rem" }}>
            Пробная попытка
          </Link>
        )}
        <Link to="/cabinet" className="dash-card-link" style={{ marginLeft: "0.75rem" }}>
          В кабинет
        </Link>
      </div>

      {test.tickets.map((ticket, ti) => (
        <div key={ticket.id} className="dash-page-card dash-form dash-ticket">
          <h2>
            Билет №{ti + 1}{" "}
            {ticket.complete ? (
              <span className="dash-pill-ok">заполнен</span>
            ) : (
              <span className="dash-pill-draft">черновик</span>
            )}
          </h2>
          <form onSubmit={(e) => void saveTicket(ticket.id, e)}>
            {ticket.questions.map((q) => (
              <div key={q.id}>
                <h3>Вопрос {q.position}</h3>
                <label>Формулировка</label>
                <textarea name={`q${q.position}_text`} defaultValue={q.text} required />
                <div className="dash-choice-grid">
                  <div>
                    <label>A</label>
                    <input name={`q${q.position}_a`} defaultValue={q.option_a} required />
                  </div>
                  <div>
                    <label>B</label>
                    <input name={`q${q.position}_b`} defaultValue={q.option_b} required />
                  </div>
                  <div>
                    <label>C</label>
                    <input name={`q${q.position}_c`} defaultValue={q.option_c} required />
                  </div>
                  <div>
                    <label>D</label>
                    <input name={`q${q.position}_d`} defaultValue={q.option_d} required />
                  </div>
                </div>
                <label>Верный ответ</label>
                <select name={`q${q.position}_correct`} defaultValue={indexToLetter(q.correct_index)}>
                  {CORRECT_OPTIONS.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </select>
              </div>
            ))}
            <button
              type="submit"
              className="dash-exam-btn"
              style={{ border: "none", cursor: "pointer", marginTop: "1rem" }}
              disabled={saving}
            >
              Сохранить билет
            </button>
          </form>
          <button
            type="button"
            className="dash-btn-danger"
            onClick={() => void deleteTicket(ticket.id)}
          >
            Удалить билет
          </button>
        </div>
      ))}
    </DashboardLayout>
  );
}
