import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { axiosErrorMessage, deleteReact, postReact, putReact } from "../api/getReact";
import DashboardLayout from "../layout/DashboardLayout";
import { useGetReact } from "../hooks/useGetReact";
import type { QuestionSave, TestEdit } from "../types/api";
import {
  indexToLetter,
  labelsForCount,
  MAX_OPTION_COUNT,
  MIN_OPTION_COUNT,
  normalizeOptionCount,
} from "../utils/questionOptions";

export default function TestEditPage() {
  const { testId } = useParams();
  const id = Number(testId);
  const editPath = id ? `/tests/${id}` : null;
  const { data: test, setData: setTest, error, loading } = useGetReact<TestEdit>(editPath, Boolean(id));
  const [actionError, setActionError] = useState("");
  const [saving, setSaving] = useState(false);
  const [optionCounts, setOptionCounts] = useState<Record<number, number>>({});

  useEffect(() => {
    if (test) {
      setOptionCounts(
        Object.fromEntries(
          test.tickets.map((t) => [t.id, normalizeOptionCount(t.option_count)])
        )
      );
    }
  }, [test]);

  const addTicket = async () => {
    if (!id) return;
    try {
      setTest(await postReact<TestEdit>(`/tests/${id}/tickets`));
      setActionError("");
    } catch (e) {
      setActionError(axiosErrorMessage(e));
    }
  };

  const deleteTicket = async (ticketId: number) => {
    if (!id || !confirm("Удалить билет?")) return;
    try {
      setTest(await deleteReact<TestEdit>(`/tests/${id}/tickets/${ticketId}`));
      setActionError("");
    } catch (e) {
      setActionError(axiosErrorMessage(e));
    }
  };

  const saveTicket = async (ticketId: number, e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!id || !test) return;
    setSaving(true);
    const fd = new FormData(e.currentTarget);
    const questions: QuestionSave[] = [];
    const option_count = normalizeOptionCount(Number(fd.get("option_count") ?? 4));
    for (let pos = 1; pos <= test.questions_per_ticket; pos++) {
      questions.push({
        position: pos,
        option_count,
        text: String(fd.get(`q${pos}_text`) || ""),
        option_a: String(fd.get(`q${pos}_a`) || ""),
        option_b: String(fd.get(`q${pos}_b`) || ""),
        option_c: option_count >= 3 ? String(fd.get(`q${pos}_c`) || "") : "",
        option_d: option_count >= 4 ? String(fd.get(`q${pos}_d`) || "") : "",
        correct: String(fd.get(`q${pos}_correct`) || "A"),
      });
    }
    try {
      setTest(
        await putReact<TestEdit>(`/tests/${id}/tickets/${ticketId}`, { option_count, questions })
      );
      setActionError("");
    } catch (err) {
      setActionError(axiosErrorMessage(err));
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

      {test.tickets.map((ticket, ti) => {
        const optionCount = optionCounts[ticket.id] ?? normalizeOptionCount(ticket.option_count);
        const labels = labelsForCount(optionCount);
        const optionInputs = (
          [
            { key: "a", label: "A" },
            { key: "b", label: "B" },
            { key: "c", label: "C" },
            { key: "d", label: "D" },
          ] as const
        ).slice(0, optionCount);
        return (
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
            <label htmlFor={`opt-count-${ticket.id}`}>Количество вариантов ответа</label>
            <select
              id={`opt-count-${ticket.id}`}
              name="option_count"
              value={optionCount}
              onChange={(e) =>
                setOptionCounts((prev) => ({
                  ...prev,
                  [ticket.id]: normalizeOptionCount(Number(e.target.value)),
                }))
              }
            >
              {Array.from(
                { length: MAX_OPTION_COUNT - MIN_OPTION_COUNT + 1 },
                (_, i) => MIN_OPTION_COUNT + i
              ).map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
            {ticket.questions.map((q) => (
              <div key={q.id}>
                <h3>Вопрос {q.position}</h3>
                <label>Формулировка</label>
                <textarea name={`q${q.position}_text`} defaultValue={q.text} required />
                <div className="dash-choice-grid">
                  {optionInputs.map(({ key, label }) => (
                    <div key={key}>
                      <label>{label}</label>
                      <input
                        name={`q${q.position}_${key}`}
                        defaultValue={q[`option_${key}` as keyof typeof q] as string}
                        required
                      />
                    </div>
                  ))}
                </div>
                <label>Верный ответ</label>
                <select name={`q${q.position}_correct`} defaultValue={indexToLetter(q.correct_index)}>
                  {labels.map((l) => (
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
              Договорились!
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
        );
      })}
    </DashboardLayout>
  );
}
