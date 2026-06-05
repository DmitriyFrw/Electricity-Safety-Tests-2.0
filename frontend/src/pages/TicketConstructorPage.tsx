import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { axiosErrorMessage, deleteReact, postReact, putReact } from "../api/getReact";
import RichTextEditor from "../components/RichTextEditor";
import SidebarPortal from "../components/SidebarPortal";
import DashboardLayout from "../layout/DashboardLayout";
import { useGetReact } from "../hooks/useGetReact";
import type { QuestionSave, TestEdit, TestListItem } from "../types/api";
import {
  clampCorrectLetter,
  indexToLetter,
  labelsForCount,
  MAX_OPTION_COUNT,
  MIN_OPTION_COUNT,
  normalizeOptionCount,
  optionFieldsForQuestion,
} from "../utils/questionOptions";
import {
  importedRowsToDrafts,
  parseQuestionsFromFile,
  TICKET_IMPORT_ACCEPT,
  type QuestionDraft,
} from "../utils/ticketImport";

const MAX_QUESTIONS = 10;

type TicketDraft = {
  id: number;
  position: number;
  title: string;
  option_count: number;
  questions: QuestionDraft[];
};

function renumberQuestions(questions: QuestionDraft[]): QuestionDraft[] {
  return questions.map((q, index) => ({ ...q, position: index + 1 }));
}

function emptyQuestion(position: number, optionCount: number): QuestionDraft {
  return {
    position,
    text: "",
    option_a: "",
    option_b: "",
    option_c: "",
    option_d: "",
    correct: clampCorrectLetter("A", optionCount),
  };
}

function testToDrafts(test: TestEdit): TicketDraft[] {
  return test.tickets.map((t) => {
    const option_count = normalizeOptionCount(t.option_count);
    const questions =
      t.questions.length > 0
        ? t.questions.map((q) => ({
            position: q.position,
            text: q.text,
            option_a: q.option_a,
            option_b: q.option_b,
            option_c: q.option_c,
            option_d: q.option_d,
            correct: clampCorrectLetter(indexToLetter(q.correct_index), option_count),
          }))
        : [emptyQuestion(1, option_count)];
    return {
      id: t.id,
      position: t.position,
      title: t.title ?? "",
      option_count,
      questions,
    };
  });
}

function questionHasContent(q: QuestionDraft, optionCount: number): boolean {
  const fields = optionFieldsForQuestion(q, optionCount);
  if (q.text.replace(/<[^>]+>/g, "").trim()) return true;
  return fields.some((f) => f.field && q[f.field].replace(/<[^>]+>/g, "").trim());
}

function defaultVisibleCount(draft: TicketDraft): number {
  let last = 1;
  draft.questions.forEach((q, idx) => {
    if (questionHasContent(q, draft.option_count)) last = idx + 1;
  });
  return Math.min(MAX_QUESTIONS, Math.max(1, last, draft.questions.length));
}

function scrollToElement(id: string) {
  requestAnimationFrame(() => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function NumberCircleNav({
  ariaLabel,
  items,
  activeIndex,
  onSelect,
  showTrailingEllipsis,
  variant = "inline",
}: {
  ariaLabel: string;
  items: { key: string | number; label: number; filled?: boolean }[];
  activeIndex: number | null;
  onSelect: (index: number) => void;
  showTrailingEllipsis?: boolean;
  variant?: "inline" | "sidebar";
}) {
  if (items.length === 0) return null;
  return (
    <nav
      className={`constructor-number-nav${variant === "sidebar" ? " constructor-number-nav-sidebar" : ""}`}
      aria-label={ariaLabel}
    >
      {items.map((item, index) => (
        <button
          key={item.key}
          type="button"
          className={[
            "constructor-number-pill",
            activeIndex === index ? "constructor-number-pill-active" : "",
            item.filled && activeIndex !== index ? "constructor-number-pill-filled" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          title={`${ariaLabel} ${item.label}`}
          onClick={() => onSelect(index)}
        >
          {item.label}
        </button>
      ))}
      {showTrailingEllipsis && <span className="constructor-number-ellipsis" aria-hidden>…</span>}
    </nav>
  );
}

function ConstructorTestList() {
  const [tests, setTests] = useState<TestListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingTestId, setDeletingTestId] = useState<number | null>(null);

  useEffect(() => {
    void (async () => {
      setLoading(true);
      try {
        const items = await api.listTests();
        setTests(items.filter((t) => t.can_edit));
      } catch (e) {
        setError(axiosErrorMessage(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const onDeleteTest = async (t: TestListItem) => {
    const ok = window.confirm(
      `Удалить тест «${t.title}»? Билеты и вопросы будут удалены без возможности восстановления.`
    );
    if (!ok) return;
    setError("");
    setDeletingTestId(t.id);
    try {
      await api.deleteTest(t.id);
      setTests((prev) => prev.filter((item) => item.id !== t.id));
    } catch (e) {
      setError(axiosErrorMessage(e));
    } finally {
      setDeletingTestId(null);
    }
  };

  return (
    <>
      <p className="dash-card-note" style={{ marginBottom: "var(--spacing-4)" }}>
        Выберите тест для редактирования билетов с форматированием текста.
      </p>
      {error && <p className="auth-error">{error}</p>}
      {loading ? (
        <p className="dash-card-note">Загрузка…</p>
      ) : tests.length === 0 ? (
        <p className="dash-card-note">
          Нет доступных тестов.{" "}
          <Link to="/tests/new" className="dash-card-link">
            Создать тест
          </Link>
        </p>
      ) : (
        <ul className="constructor-test-list">
          {tests.map((t) => (
            <li key={t.id}>
              <div>
                <strong>{t.title}</strong>
                <div className="dash-card-meta">
                  Билетов: {t.ticket_count}
                  {t.ready ? " · готов" : " · черновик"}
                </div>
              </div>
              <div className="constructor-page-actions" style={{ flexShrink: 0 }}>
                <Link
                  to={`/constructor/${t.id}`}
                  className="btn btn-outline btn-sm"
                  style={{ textDecoration: "none" }}
                >
                  Открыть
                </Link>
                <button
                  type="button"
                  className="dash-btn-danger btn-sm"
                  disabled={deletingTestId === t.id}
                  onClick={() => void onDeleteTest(t)}
                >
                  {deletingTestId === t.id ? "Удаление…" : "Удалить"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
      <Link to="/tests/new" className="dash-exam-btn" style={{ marginTop: "1.5rem", display: "inline-block" }}>
        + Новый тест
      </Link>
    </>
  );
}

function TicketConfigurePanel({
  ticketId,
  draft,
  ticketComplete,
  visibleCount,
  onClose,
  onUpdateDraft,
  onSetVisibleCount,
  onSave,
  onDelete,
  saving,
  deleting,
}: {
  ticketId: number;
  draft: TicketDraft;
  ticketComplete: boolean;
  visibleCount: number;
  onClose: () => void;
  onUpdateDraft: (updater: (d: TicketDraft) => TicketDraft) => void;
  onSetVisibleCount: (n: number) => void;
  onSave: () => void;
  onDelete: () => void;
  saving: boolean;
  deleting: boolean;
}) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [importError, setImportError] = useState("");
  const [collapsedQuestions, setCollapsedQuestions] = useState<Record<number, boolean>>({});
  const [activeQuestionIndex, setActiveQuestionIndex] = useState<number | null>(null);

  useEffect(() => {
    setCollapsedQuestions({});
    setActiveQuestionIndex(null);
  }, [ticketId]);

  const questionsShown = draft.questions.slice(0, visibleCount);
  const canAddQuestion = draft.questions.length < MAX_QUESTIONS;

  const onImport = async (file: File) => {
    setImportError("");
    try {
      const rows = await parseQuestionsFromFile(file, draft.option_count);
      if (rows.length === 0) {
        setImportError("В файле не найдено вопросов");
        return;
      }
      const imported = importedRowsToDrafts(rows, draft.option_count);
      onUpdateDraft((d) => ({ ...d, questions: renumberQuestions(imported) }));
      onSetVisibleCount(imported.length);
    } catch (e) {
      setImportError(e instanceof Error ? e.message : "Не удалось прочитать файл");
    } finally {
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const addQuestion = () => {
    if (!canAddQuestion) return;
    const nextPos = draft.questions.length + 1;
    const newIndex = draft.questions.length;
    onUpdateDraft((d) => ({
      ...d,
      questions: [...d.questions, emptyQuestion(nextPos, d.option_count)],
    }));
    onSetVisibleCount(Math.min(MAX_QUESTIONS, visibleCount + 1));
    setCollapsedQuestions((prev) => ({ ...prev, [newIndex]: false }));
    setActiveQuestionIndex(newIndex);
    scrollToElement(`constructor-q-${ticketId}-${newIndex}`);
  };

  const goToQuestion = (qi: number) => {
    if (qi + 1 > visibleCount) {
      onSetVisibleCount(Math.min(MAX_QUESTIONS, qi + 1));
    }
    setCollapsedQuestions((prev) => ({ ...prev, [qi]: false }));
    setActiveQuestionIndex(qi);
    scrollToElement(`constructor-q-${ticketId}-${qi}`);
  };

  const toggleQuestionCollapsed = (qi: number) => {
    setCollapsedQuestions((prev) => ({ ...prev, [qi]: !prev[qi] }));
  };

  const removeQuestion = (qi: number) => {
    if (draft.questions.length <= 1) return;
    if (!confirm(`Удалить вопрос ${qi + 1}?`)) return;
    const nextLen = draft.questions.length - 1;
    onUpdateDraft((d) => ({
      ...d,
      questions: renumberQuestions(d.questions.filter((_, index) => index !== qi)),
    }));
    onSetVisibleCount(Math.max(1, Math.min(visibleCount, nextLen)));
    setCollapsedQuestions({});
    setActiveQuestionIndex(null);
  };

  return (
    <div
      id={`constructor-panel-${ticketId}`}
      className="dash-page-card dash-form constructor-configure-panel"
    >
      <div className="constructor-ticket-head">
        <h2 className="dash-section-title" style={{ margin: 0 }}>
          {draft.title.trim() || `Билет ${draft.position}`}
          {ticketComplete ? (
            <span className="dash-pill-ok"> заполнен</span>
          ) : (
            <span className="dash-pill-draft"> черновик</span>
          )}
        </h2>
        <button type="button" className="dash-link-btn" onClick={onClose}>
          Свернуть
        </button>
      </div>

      <label htmlFor={`ticket-options-${ticketId}`}>Количество вариантов ответа</label>
      <select
        id={`ticket-options-${ticketId}`}
        className="constructor-ticket-title-input constructor-option-count-select"
        value={draft.option_count}
        onChange={(e) => {
          const option_count = normalizeOptionCount(Number(e.target.value));
          onUpdateDraft((d) => ({
            ...d,
            option_count,
            questions: d.questions.map((item) => ({
              ...item,
              correct: clampCorrectLetter(item.correct, option_count),
            })),
          }));
        }}
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

      <div className="constructor-questions-toolbar">
        <h3 className="constructor-questions-toolbar-title">Список вопросов</h3>
        <div className="constructor-page-actions">
          <input
            ref={fileRef}
            type="file"
            accept={TICKET_IMPORT_ACCEPT}
            className="constructor-file-input"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void onImport(f);
            }}
          />
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => fileRef.current?.click()}
          >
            Загрузить из файла
          </button>
        </div>
      </div>
      {importError && <p className="auth-error">{importError}</p>}
      <p className="dash-card-note constructor-import-hint">
        Поддерживаются TXT, CSV, TSV и Excel (.xlsx, .xls). Колонки: формулировка, варианты A–D,
        верный ответ (необязательно).
      </p>

      <NumberCircleNav
        ariaLabel="Вопрос"
        items={draft.questions.map((q, qi) => ({
          key: qi,
          label: q.position,
          filled: questionHasContent(q, draft.option_count),
        }))}
        activeIndex={activeQuestionIndex}
        onSelect={goToQuestion}
        showTrailingEllipsis={canAddQuestion}
      />

      {questionsShown.map((q, qi) => {
        const collapsed = Boolean(collapsedQuestions[qi]);
        const optionFields = optionFieldsForQuestion(q, draft.option_count);
        const correctLabels = labelsForCount(draft.option_count);
        return (
          <div
            key={`${ticketId}-q-${qi}`}
            id={`constructor-q-${ticketId}-${qi}`}
            className={`constructor-question-block${collapsed ? " constructor-question-block-collapsed" : ""}`}
          >
            <div className="constructor-question-head">
              <h4 className="constructor-question-title">Вопрос {q.position}</h4>
              <div className="constructor-question-head-actions">
                <button
                  type="button"
                  className="dash-link-btn"
                  onClick={() => toggleQuestionCollapsed(qi)}
                >
                  {collapsed ? "Развернуть" : "Свернуть"}
                </button>
                {draft.questions.length > 1 && (
                  <button
                    type="button"
                    className="dash-btn-danger btn-sm"
                    onClick={() => removeQuestion(qi)}
                  >
                    Удалить вопрос
                  </button>
                )}
              </div>
            </div>
            {!collapsed && (
            <div className="constructor-question-layout">
              <div className="constructor-question-formulation">
                <RichTextEditor
                  label="Формулировка"
                  value={q.text}
                  onChange={(html) =>
                    onUpdateDraft((d) => ({
                      ...d,
                      questions: d.questions.map((item, idx) =>
                        idx === qi ? { ...item, text: html } : item
                      ),
                    }))
                  }
                  minHeight={120}
                />
                <label htmlFor={`correct-${ticketId}-${q.position}`}>Верный ответ</label>
                <select
                  id={`correct-${ticketId}-${q.position}`}
                  className="constructor-ticket-title-input constructor-option-count-select"
                  value={q.correct}
                  onChange={(e) =>
                    onUpdateDraft((d) => ({
                      ...d,
                      questions: d.questions.map((item, idx) =>
                        idx === qi ? { ...item, correct: e.target.value } : item
                      ),
                    }))
                  }
                >
                  {correctLabels.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </select>
              </div>
              <div className="constructor-question-options">
                {optionFields.map(({ key, label, field }) => (
                  <RichTextEditor
                    key={key}
                    label={`Вариант ${label}`}
                    value={q[field]}
                    minHeight={56}
                    onChange={(html) =>
                      onUpdateDraft((d) => ({
                        ...d,
                        questions: d.questions.map((item, idx) =>
                          idx === qi ? { ...item, [field]: html } : item
                        ),
                      }))
                    }
                  />
                ))}
              </div>
            </div>
            )}
          </div>
        );
      })}

      {canAddQuestion && (
        <button type="button" className="btn btn-outline" onClick={addQuestion}>
          Добавить вопрос
        </button>
      )}

      <div className="constructor-actions">
        <button
          type="button"
          className="dash-exam-btn"
          disabled={saving}
          onClick={() => void onSave()}
        >
          {saving ? "Сохранение…" : "Договорились!"}
        </button>
        <button
          type="button"
          className="dash-btn-danger"
          disabled={deleting}
          onClick={() => void onDelete()}
        >
          {deleting ? "Удаление…" : "Удалить билет"}
        </button>
      </div>
    </div>
  );
}

function ConstructorEditor({ testId }: { testId: number }) {
  const navigate = useNavigate();
  const editPath = `/tests/${testId}`;
  const { data: test, setData: setTest, error, loading } = useGetReact<TestEdit>(editPath, true);
  const [drafts, setDrafts] = useState<TicketDraft[]>([]);
  const [activeTicketId, setActiveTicketId] = useState<number | null>(null);
  const [visibleByTicket, setVisibleByTicket] = useState<Record<number, number>>({});
  const [actionError, setActionError] = useState("");
  const [savingId, setSavingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (test) {
      const next = testToDrafts(test);
      setDrafts(next);
      setVisibleByTicket((prev) => {
        const merged = { ...prev };
        for (const d of next) {
          if (merged[d.id] === undefined) merged[d.id] = defaultVisibleCount(d);
        }
        return merged;
      });
    }
  }, [test]);

  const updateDraft = useCallback((ticketId: number, updater: (d: TicketDraft) => TicketDraft) => {
    setDrafts((prev) => prev.map((d) => (d.id === ticketId ? updater(d) : d)));
  }, []);

  const addTicket = async () => {
    try {
      const updated = await postReact<TestEdit>(`/tests/${testId}/tickets`);
      setTest(updated);
      setActionError("");
      const last = updated.tickets[updated.tickets.length - 1];
      if (last) {
        setActiveTicketId(last.id);
        setVisibleByTicket((v) => ({ ...v, [last.id]: 1 }));
      }
    } catch (e) {
      setActionError(axiosErrorMessage(e));
    }
  };

  const deleteTicket = async (ticketId: number) => {
    const ticket = test?.tickets.find((t) => t.id === ticketId);
    const draft = drafts.find((d) => d.id === ticketId);
    const label = draft?.title.trim() || (ticket ? `Билет ${ticket.position}` : "билет");
    if (!confirm(`Удалить «${label}»? Действие нельзя отменить.`)) return;
    setDeletingId(ticketId);
    setActionError("");
    try {
      setTest(await deleteReact<TestEdit>(`/tests/${testId}/tickets/${ticketId}`));
      setMessage("Билет удалён");
      if (activeTicketId === ticketId) setActiveTicketId(null);
    } catch (e) {
      setActionError(axiosErrorMessage(e));
    } finally {
      setDeletingId(null);
    }
  };

  const saveTicket = async (ticketId: number) => {
    const draft = drafts.find((d) => d.id === ticketId);
    if (!draft || !test) return;
    const count = visibleByTicket[ticketId] ?? draft.questions.length;
    const slice = draft.questions.slice(0, count);
    setSavingId(ticketId);
    setMessage("");
    setActionError("");
    const questions: QuestionSave[] = renumberQuestions(slice).map((q) => ({
      position: q.position,
      text: q.text,
      option_a: q.option_a,
      option_b: q.option_b,
      option_c: q.option_c,
      option_d: q.option_d,
      correct: q.correct,
    }));
    try {
      setTest(
        await putReact<TestEdit>(`/tests/${testId}/tickets/${ticketId}`, {
          title: draft.title.trim() || `Билет ${draft.position}`,
          option_count: draft.option_count,
          questions,
        })
      );
      setMessage("Билет сохранён");
    } catch (err) {
      setActionError(axiosErrorMessage(err));
    } finally {
      setSavingId(null);
    }
  };

  if (loading || !test) {
    return <p className="dash-card-note">{error || "Загрузка…"}</p>;
  }

  const displayError = actionError || error;
  const activeDraft = activeTicketId ? drafts.find((d) => d.id === activeTicketId) : null;
  const activeTicket = activeTicketId ? test.tickets.find((t) => t.id === activeTicketId) : null;
  const activeTicketIndex =
    activeTicketId != null ? test.tickets.findIndex((t) => t.id === activeTicketId) : -1;

  const activateTicket = (ticketId: number, scrollToPanel = false) => {
    const opening = activeTicketId !== ticketId;
    setActiveTicketId(ticketId);
    const draft = drafts.find((d) => d.id === ticketId);
    if (draft && visibleByTicket[ticketId] === undefined) {
      setVisibleByTicket((v) => ({
        ...v,
        [ticketId]: defaultVisibleCount(draft),
      }));
    }
    scrollToElement(`constructor-ticket-${ticketId}`);
    if (scrollToPanel || opening) {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          scrollToElement(`constructor-panel-${ticketId}`);
        });
      });
    }
  };

  return (
    <>
      {test.tickets.length > 0 && (
        <SidebarPortal>
          <div className="sidebar-constructor-tickets">
            <p className="sidebar-constructor-tickets-title">Билеты</p>
            <NumberCircleNav
              variant="sidebar"
              ariaLabel="Билет"
              items={test.tickets.map((ticket) => {
                const draft = drafts.find((d) => d.id === ticket.id);
                return {
                  key: ticket.id,
                  label: ticket.position,
                  filled:
                    ticket.complete ||
                    Boolean(
                      draft &&
                        draft.questions.some((q) => questionHasContent(q, draft.option_count))
                    ),
                };
              })}
              activeIndex={activeTicketIndex >= 0 ? activeTicketIndex : null}
              onSelect={(index) => {
                const ticket = test.tickets[index];
                if (ticket) activateTicket(ticket.id, true);
              }}
              showTrailingEllipsis={test.tickets.length < test.max_tickets}
            />
          </div>
        </SidebarPortal>
      )}

      <div className="dash-page-card">
        <h1>{test.title}</h1>
        <p className="dash-card-meta">
          Билетов {test.tickets.length}/{test.max_tickets}
          {test.ready ? " · готов к сдаче" : " · заполните все билеты (по 10 вопросов в каждом)"}
        </p>
        {displayError && <p className="auth-error">{displayError}</p>}
        {message && <p className="dash-card-note">{message}</p>}
        <Link to="/constructor" className="dash-card-link" style={{ display: "inline-block", marginBottom: "var(--spacing-4)" }}>
          ← К списку тестов
        </Link>
      </div>

      <div className="dash-page-card constructor-tickets-card">
        <ul className="constructor-ticket-rows">
          {test.tickets.map((ticket) => {
            const draft = drafts.find((d) => d.id === ticket.id);
            const label = draft?.title.trim() || `Билет ${ticket.position}`;
            const isActive = activeTicketId === ticket.id;
            return (
              <li
                key={ticket.id}
                id={`constructor-ticket-${ticket.id}`}
                className={isActive ? "constructor-ticket-row-active" : ""}
              >
                <div className="constructor-ticket-row-main">
                  <strong>{label}</strong>
                  {ticket.complete ? (
                    <span className="dash-pill-ok">заполнен</span>
                  ) : (
                    <span className="dash-pill-draft">черновик</span>
                  )}
                </div>
                <div className="constructor-page-actions">
                  <button
                    type="button"
                    className={isActive ? "dash-exam-btn" : "btn btn-outline btn-sm"}
                    style={isActive ? { border: "none", cursor: "pointer" } : undefined}
                    onClick={() => activateTicket(ticket.id, true)}
                  >
                    {isActive ? "Настраивается…" : "Настроить"}
                  </button>
                  <button
                    type="button"
                    className="dash-btn-danger btn-sm"
                    disabled={deletingId === ticket.id}
                    onClick={() => void deleteTicket(ticket.id)}
                  >
                    Удалить
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
        <button
          type="button"
          className="dash-exam-btn"
          style={{ border: "none", cursor: "pointer", marginTop: "var(--spacing-4)" }}
          disabled={test.tickets.length >= test.max_tickets}
          onClick={() => void addTicket()}
        >
          Добавить билет
        </button>
      </div>

      {activeDraft && activeTicket && (
        <TicketConfigurePanel
          ticketId={activeTicket.id}
          draft={activeDraft}
          ticketComplete={activeTicket.complete}
          visibleCount={visibleByTicket[activeTicket.id] ?? defaultVisibleCount(activeDraft)}
          onClose={() => setActiveTicketId(null)}
          onUpdateDraft={(updater) => updateDraft(activeTicket.id, updater)}
          onSetVisibleCount={(n) =>
            setVisibleByTicket((v) => ({ ...v, [activeTicket.id]: n }))
          }
          onSave={() => void saveTicket(activeTicket.id)}
          onDelete={() => void deleteTicket(activeTicket.id)}
          saving={savingId === activeTicket.id}
          deleting={deletingId === activeTicket.id}
        />
      )}

      <button
        type="button"
        className="dash-link-btn"
        onClick={() => navigate("/constructor")}
      >
        Закрыть редактор
      </button>
    </>
  );
}

export default function TicketConstructorPage() {
  const { testId } = useParams();
  const id = testId ? Number(testId) : null;

  return (
    <DashboardLayout active="constructor">
      <h1 className="dash-section-title">Конструктор билетов</h1>
      {id && !Number.isNaN(id) ? <ConstructorEditor testId={id} /> : <ConstructorTestList />}
    </DashboardLayout>
  );
}
