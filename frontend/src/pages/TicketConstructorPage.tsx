import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import CreateTestDialog from "../components/CreateTestDialog";
import { api } from "../api/client";
import { axiosErrorMessage, deleteReact, postReact, putReact } from "../api/getReact";
import { safetyGroupLabel } from "../constants/safetyGroups";
import RichTextEditor from "../components/RichTextEditor";
import ConstructorCatalog from "../components/ConstructorCatalog";
import SidebarPortal from "../components/SidebarPortal";
import ConstructorLayout from "../layout/ConstructorLayout";
import { useGetReact } from "../hooks/useGetReact";
import type { QuestionSave, TestEdit } from "../types/api";
import {
  clampCorrectLetters,
  formatCorrectLetters,
  indexToLetter,
  labelsForCount,
  MAX_OPTION_COUNT,
  MIN_OPTION_COUNT,
  normalizeOptionCount,
  optionFieldsForQuestion,
  toggleCorrectLetter,
} from "../utils/questionOptions";
import {
  importedRowsToDrafts,
  parseQuestionsFromFile,
  TICKET_IMPORT_ACCEPT,
  type QuestionDraft,
} from "../utils/ticketImport";
import {
  exportTicketToFile,
  TICKET_EXPORT_FORMATS,
  type TicketExportFormat,
} from "../utils/ticketExport";

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

function questionCorrectLetters(
  q: { correct_index: number; correct_indexes?: number[] },
  optionCount: number
): string[] {
  const letters =
    q.correct_indexes && q.correct_indexes.length
      ? q.correct_indexes.map((i) => indexToLetter(i))
      : [indexToLetter(q.correct_index)];
  return clampCorrectLetters(letters, optionCount);
}

function emptyQuestion(position: number, optionCount: number): QuestionDraft {
  const option_count = normalizeOptionCount(optionCount);
  return {
    position,
    option_count,
    text: "",
    option_a: "",
    option_b: "",
    option_c: "",
    option_d: "",
    correct: ["A"],
  };
}

function testToDrafts(test: TestEdit): TicketDraft[] {
  return test.tickets.map((t) => {
    const ticketDefault = normalizeOptionCount(t.option_count);
    const questions =
      t.questions.length > 0
        ? t.questions.map((q) => {
            const option_count = normalizeOptionCount(q.option_count ?? ticketDefault);
            return {
              position: q.position,
              option_count,
              text: q.text,
              option_a: q.option_a,
              option_b: q.option_b,
              option_c: q.option_c,
              option_d: q.option_d,
              correct: questionCorrectLetters(q, option_count),
            };
          })
        : [emptyQuestion(1, ticketDefault)];
    return {
      id: t.id,
      position: t.position,
      title: t.title ?? "",
      option_count: ticketDefault,
      questions,
    };
  });
}

function questionHasContent(q: QuestionDraft): boolean {
  const fields = optionFieldsForQuestion(q);
  if (q.text.replace(/<[^>]+>/g, "").trim()) return true;
  return fields.some((f) => f.field && q[f.field].replace(/<[^>]+>/g, "").trim());
}

function defaultVisibleCount(draft: TicketDraft): number {
  let last = 1;
  draft.questions.forEach((q, idx) => {
    if (questionHasContent(q)) last = idx + 1;
  });
  return Math.min(MAX_QUESTIONS, Math.max(1, last, draft.questions.length));
}

function scrollToElement(id: string) {
  requestAnimationFrame(() => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function TicketPencilIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden focusable="false">
      <path
        fill="currentColor"
        d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zm2.92 2.08H5v-.92l8.06-8.06.92.92L5.92 19.33zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"
      />
    </svg>
  );
}

function TicketDeleteIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden focusable="false">
      <path
        fill="currentColor"
        d="M18.3 5.71a1 1 0 0 0-1.41 0L12 10.59 7.11 5.7A1 1 0 1 0 5.7 7.11L10.59 12l-4.9 4.89a1 1 0 1 0 1.41 1.42L12 13.41l4.89 4.9a1 1 0 0 0 1.42-1.42L13.41 12l4.9-4.89a1 1 0 0 0-.01-1.4z"
      />
    </svg>
  );
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
  const [exportFormat, setExportFormat] = useState<TicketExportFormat>("xlsx");
  const [exportError, setExportError] = useState("");
  const [collapsedQuestions, setCollapsedQuestions] = useState<Record<number, boolean>>({});
  const [activeQuestionIndex, setActiveQuestionIndex] = useState<number | null>(null);

  useEffect(() => {
    setCollapsedQuestions({});
    setActiveQuestionIndex(null);
  }, [ticketId]);

  const questionsShown = draft.questions.slice(0, visibleCount);
  const canAddQuestion = draft.questions.length < MAX_QUESTIONS;

  const onExport = async () => {
    setExportError("");
    try {
      const slice = draft.questions.slice(0, visibleCount);
      await exportTicketToFile(
        renumberQuestions(slice),
        exportFormat,
        draft.title.trim() || `Билет ${draft.position}`
      );
    } catch (e) {
      setExportError(e instanceof Error ? e.message : "Не удалось выгрузить файл");
    }
  };

  const onImport = async (file: File) => {
    setImportError("");
    try {
      const rows = await parseQuestionsFromFile(file, draft.option_count);
      if (rows.length === 0) {
        setImportError("В файле не найдено вопросов");
        return;
      }
      const imported = importedRowsToDrafts(rows);
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
      className="mockup-page-card constructor-configure-panel"
    >
      <div className="constructor-ticket-head">
        <h2 style={{ margin: 0 }}>
          {draft.title.trim() || `Билет ${draft.position}`}
          {ticketComplete ? (
            <span className="mockup-pill mockup-pill--ok"> заполнен</span>
          ) : (
            <span className="mockup-pill mockup-pill--draft"> черновик</span>
          )}
        </h2>
        <button type="button" className="mockup-link mockup-link--btn" onClick={onClose}>
          ← К списку билетов
        </button>
      </div>

      <div className="constructor-questions-header">
        <h3 className="constructor-questions-list-title">Список вопросов</h3>
        <div className="constructor-file-actions">
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
            className="mockup-btn mockup-btn--outline mockup-btn--sm"
            onClick={() => fileRef.current?.click()}
          >
            Загрузить из файла
          </button>
          <button
            type="button"
            className="mockup-btn mockup-btn--outline mockup-btn--sm"
            onClick={() => void onExport()}
          >
            Выгрузить в файл
          </button>
          <select
            className="constructor-ticket-title-input constructor-export-format-select"
            value={exportFormat}
            aria-label="Формат выгрузки"
            onChange={(e) => setExportFormat(e.target.value as TicketExportFormat)}
          >
            {TICKET_EXPORT_FORMATS.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label}
              </option>
            ))}
          </select>
        </div>
      </div>
      {importError && <p className="auth-error">{importError}</p>}
      {exportError && <p className="auth-error">{exportError}</p>}
      <p className="mockup-muted constructor-import-hint">
        Поддерживаются TXT, CSV, TSV и Excel (.xlsx, .xls). Колонки: формулировка, варианты A–D,
        верные ответы, кол-во вариантов (2–4, необязательно). У каждого вопроса можно задать своё
        число вариантов.
      </p>

      <NumberCircleNav
        ariaLabel="Вопрос"
        items={draft.questions.map((q, qi) => ({
          key: qi,
          label: q.position,
          filled: questionHasContent(q),
        }))}
        activeIndex={activeQuestionIndex}
        onSelect={goToQuestion}
        showTrailingEllipsis={canAddQuestion}
      />

      {questionsShown.map((q, qi) => {
        const collapsed = Boolean(collapsedQuestions[qi]);
        const optionFields = optionFieldsForQuestion(q);
        const correctLabels = labelsForCount(q.option_count);
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
                  className="mockup-link mockup-link--btn"
                  onClick={() => toggleQuestionCollapsed(qi)}
                >
                  {collapsed ? "Развернуть" : "Свернуть"}
                </button>
                {draft.questions.length > 1 && (
                  <button
                    type="button"
                    className="mockup-btn mockup-btn--danger mockup-btn--sm"
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
                <label htmlFor={`question-options-${ticketId}-${q.position}`}>
                  Количество вариантов ответа
                </label>
                <select
                  id={`question-options-${ticketId}-${q.position}`}
                  className="constructor-ticket-title-input constructor-option-count-select"
                  value={q.option_count}
                  onChange={(e) => {
                    const option_count = normalizeOptionCount(Number(e.target.value));
                    onUpdateDraft((d) => ({
                      ...d,
                      questions: d.questions.map((item, idx) =>
                        idx === qi
                          ? {
                              ...item,
                              option_count,
                              correct: clampCorrectLetters(item.correct, option_count),
                            }
                          : item
                      ),
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
                <fieldset className="constructor-correct-fieldset">
                  <legend>Верные ответы</legend>
                  <div className="constructor-correct-options">
                    {correctLabels.map((label) => (
                      <label key={label} className="constructor-correct-option">
                        <input
                          type="checkbox"
                          checked={q.correct.includes(label)}
                          onChange={() =>
                            onUpdateDraft((d) => ({
                              ...d,
                              questions: d.questions.map((item, idx) =>
                                idx === qi
                                  ? {
                                      ...item,
                                      correct: toggleCorrectLetter(
                                        item.correct,
                                        label,
                                        item.option_count
                                      ),
                                    }
                                  : item
                              ),
                            }))
                          }
                        />
                        <span>{label}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>
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
        <button type="button" className="mockup-btn mockup-btn--outline" onClick={addQuestion}>
          Добавить вопрос
        </button>
      )}

      <div className="constructor-actions">
        <button
          type="button"
          className="mockup-btn mockup-btn--primary"
          disabled={saving}
          onClick={() => void onSave()}
        >
          {saving ? "Сохранение…" : "Договорились!"}
        </button>
        <button
          type="button"
          className="mockup-btn mockup-btn--danger"
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
  const { ticketId: ticketIdParam } = useParams();
  const editingTicketId =
    ticketIdParam && !Number.isNaN(Number(ticketIdParam)) ? Number(ticketIdParam) : null;
  const editPath = `/tests/${testId}`;
  const { data: test, setData: setTest, error, loading } = useGetReact<TestEdit>(editPath, true);
  const [drafts, setDrafts] = useState<TicketDraft[]>([]);
  const [visibleByTicket, setVisibleByTicket] = useState<Record<number, number>>({});
  const [actionError, setActionError] = useState("");
  const [savingId, setSavingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);

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

  useEffect(() => {
    if (editingTicketId == null) return;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [editingTicketId]);

  useEffect(() => {
    if (!test || editingTicketId == null) return;
    const exists = test.tickets.some((t) => t.id === editingTicketId);
    if (!exists) {
      navigate(`/constructor/${testId}`, { replace: true });
      return;
    }
    const draft = drafts.find((d) => d.id === editingTicketId);
    if (draft && visibleByTicket[editingTicketId] === undefined) {
      setVisibleByTicket((v) => ({
        ...v,
        [editingTicketId]: defaultVisibleCount(draft),
      }));
    }
  }, [test, editingTicketId, testId, navigate, drafts, visibleByTicket]);

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
        setVisibleByTicket((v) => ({ ...v, [last.id]: 1 }));
        navigate(`/constructor/${testId}/tickets/${last.id}`);
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
      if (editingTicketId === ticketId) navigate(`/constructor/${testId}`);
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
      option_count: q.option_count,
      text: q.text,
      option_a: q.option_a,
      option_b: q.option_b,
      option_c: q.option_c,
      option_d: q.option_d,
      correct: formatCorrectLetters(q.correct),
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
    return <p className="mockup-muted">{error || "Загрузка…"}</p>;
  }

  const displayError = actionError || error;
  const activeDraft = editingTicketId ? drafts.find((d) => d.id === editingTicketId) : null;
  const activeTicket = editingTicketId ? test.tickets.find((t) => t.id === editingTicketId) : null;
  const activeTicketIndex =
    editingTicketId != null ? test.tickets.findIndex((t) => t.id === editingTicketId) : -1;
  const isEditingTicket = editingTicketId != null && activeDraft != null && activeTicket != null;

  const openTicket = (ticketId: number) => {
    const draft = drafts.find((d) => d.id === ticketId);
    if (draft && visibleByTicket[ticketId] === undefined) {
      setVisibleByTicket((v) => ({
        ...v,
        [ticketId]: defaultVisibleCount(draft),
      }));
    }
    navigate(`/constructor/${testId}/tickets/${ticketId}`);
  };

  const closeTicket = () => navigate(`/constructor/${testId}`);

  const updateTestSettings = async (patch: {
    random_ticket_order?: boolean;
    random_option_order?: boolean;
  }) => {
    if (!test) return;
    setSettingsSaving(true);
    setActionError("");
    try {
      const updated = await api.updateTestSettings(testId, {
        random_ticket_order: patch.random_ticket_order ?? test.random_ticket_order,
        random_option_order: patch.random_option_order ?? test.random_option_order,
      });
      setTest(updated);
      if (patch.random_ticket_order !== undefined) {
        setMessage(
          updated.random_ticket_order
            ? "В экзамене билеты будут выдаваться в случайном порядке"
            : "В экзамене билеты будут выдаваться по порядку"
        );
      } else if (patch.random_option_order !== undefined) {
        setMessage(
          updated.random_option_order
            ? "Варианты ответов в каждом вопросе будут показываться в случайном порядке"
            : "Варианты ответов будут показываться в порядке редактирования"
        );
      }
    } catch (e) {
      setActionError(axiosErrorMessage(e));
    } finally {
      setSettingsSaving(false);
    }
  };

  const publishTest = async () => {
    if (!test) return;
    setPublishing(true);
    setActionError("");
    try {
      const updated = await api.publishTest(testId);
      setTest(updated);
      setMessage("Тест опубликован — доступен для экзамена и тренировки");
    } catch (e) {
      setActionError(axiosErrorMessage(e));
    } finally {
      setPublishing(false);
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
                        draft.questions.some((q) => questionHasContent(q))
                    ),
                };
              })}
              activeIndex={activeTicketIndex >= 0 ? activeTicketIndex : null}
              onSelect={(index) => {
                const ticket = test.tickets[index];
                if (ticket) openTicket(ticket.id);
              }}
              showTrailingEllipsis={test.tickets.length < test.max_tickets}
            />
          </div>
        </SidebarPortal>
      )}

      <div className="mockup-page-card">
        <h1>{test.title}</h1>
        <p className="mockup-muted">
          {safetyGroupLabel(test.safety_group)}
          {" · "}Билетов {test.tickets.length}/{test.max_tickets}
          {test.ready
            ? " · готов к сдаче"
            : test.published
              ? " · опубликован, дозаполните неготовые билеты"
              : " · черновик — заполните все билеты (по 10 вопросов), затем «Тест готов»"}
          {test.random_ticket_order ? " · случайный порядок билетов" : ""}
          {test.random_option_order ? " · случайный порядок ответов" : ""}
        </p>
        <div className="constructor-page-toolbar">
          <div className="constructor-test-settings">
            <button
              type="button"
              className={`constructor-random-order-btn${
                test.random_ticket_order ? " constructor-random-order-btn-active" : ""
              }`}
              disabled={settingsSaving}
              onClick={() =>
                void updateTestSettings({ random_ticket_order: !test.random_ticket_order })
              }
            >
              {settingsSaving
                ? "Сохранение…"
                : test.random_ticket_order
                  ? "Случайный порядок билетов: вкл (экзамен и тренировка)"
                  : "Случайный порядок билетов: выкл (по номеру билета)"}
            </button>
            <button
              type="button"
              className={`constructor-random-order-btn${
                test.random_option_order ? " constructor-random-order-btn-active" : ""
              }`}
              disabled={settingsSaving}
              onClick={() =>
                void updateTestSettings({ random_option_order: !test.random_option_order })
              }
            >
              {settingsSaving
                ? "Сохранение…"
                : test.random_option_order
                  ? "Случайный порядок ответов: вкл"
                  : "Случайный порядок ответов: выкл"}
            </button>
          </div>
          <button
            type="button"
            className={`constructor-random-order-btn${
              test.published ? " constructor-random-order-btn-active" : ""
            }`}
            disabled={publishing || test.published || !test.content_complete}
            title={
              test.published
                ? "Тест уже опубликован"
                : !test.content_complete
                  ? "Заполните все билеты теста (по 10 вопросов в каждом)"
                  : undefined
            }
            onClick={() => void publishTest()}
          >
            {publishing ? "Публикация…" : test.published ? "Тест опубликован" : "Тест готов"}
          </button>
        </div>
        {displayError && <p className="auth-error">{displayError}</p>}
        {message && <p className="mockup-flash mockup-flash--ok">{message}</p>}
        {!isEditingTicket && (
          <Link to="/constructor" className="mockup-link">
            ← К списку тестов
          </Link>
        )}
      </div>

      {!isEditingTicket && (
      <div className="mockup-page-card constructor-tickets-card">
        <ul className="constructor-ticket-grid">
          {test.tickets.map((ticket) => {
            const draft = drafts.find((d) => d.id === ticket.id);
            const label = draft?.title.trim() || `Билет ${ticket.position}`;
            return (
              <li
                key={ticket.id}
                id={`constructor-ticket-${ticket.id}`}
                className="constructor-ticket-tile"
              >
                <div className="constructor-ticket-tile-title">{label}</div>
                {ticket.complete ? (
                  <span className="constructor-ticket-tile-status mockup-pill mockup-pill--ok">заполнен</span>
                ) : (
                  <span className="constructor-ticket-tile-status mockup-pill mockup-pill--draft">черновик</span>
                )}
                <div className="constructor-ticket-tile-actions">
                  <button
                    type="button"
                    className="constructor-ticket-icon-btn constructor-ticket-icon-btn-edit"
                    title="Редактировать билет"
                    aria-label={`Редактировать ${label}`}
                    onClick={() => openTicket(ticket.id)}
                  >
                    <TicketPencilIcon />
                  </button>
                  <button
                    type="button"
                    className="constructor-ticket-icon-btn constructor-ticket-icon-btn-delete"
                    title="Удалить билет"
                    aria-label={`Удалить ${label}`}
                    disabled={deletingId === ticket.id}
                    onClick={() => void deleteTicket(ticket.id)}
                  >
                    <TicketDeleteIcon />
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
        <button
          type="button"
          className="mockup-btn mockup-btn--primary"
          style={{ marginTop: "var(--spacing-4)" }}
          disabled={test.tickets.length >= test.max_tickets}
          onClick={() => void addTicket()}
        >
          Добавить билет
        </button>
      </div>
      )}

      {isEditingTicket && (
        <TicketConfigurePanel
          ticketId={activeTicket.id}
          draft={activeDraft}
          ticketComplete={activeTicket.complete}
          visibleCount={visibleByTicket[activeTicket.id] ?? defaultVisibleCount(activeDraft)}
          onClose={closeTicket}
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

      {!isEditingTicket && (
        <button
          type="button"
          className="mockup-link mockup-link--btn"
          onClick={() => navigate("/constructor")}
        >
          Закрыть редактор
        </button>
      )}
    </>
  );
}

export default function TicketConstructorPage() {
  const { testId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [createOpen, setCreateOpen] = useState(false);
  const id = testId ? Number(testId) : null;
  const editing = id != null && !Number.isNaN(id);
  const { data: testMeta } = useGetReact<TestEdit>(
    editing ? `/tests/${id}` : null,
    Boolean(editing)
  );

  useEffect(() => {
    if (searchParams.get("create") === "1") {
      setCreateOpen(true);
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const openCreate = () => setCreateOpen(true);

  return (
    <ConstructorLayout
      editing={editing}
      title={editing && testMeta ? testMeta.title : "Конструктор билетов"}
      showCreate={!editing}
      onCreateClick={!editing ? openCreate : undefined}
    >
      {!editing && (
        <CreateTestDialog open={createOpen} onClose={() => setCreateOpen(false)} />
      )}
      {editing ? (
        <ConstructorEditor testId={id} />
      ) : (
        <ConstructorCatalog onCreateClick={openCreate} />
      )}
    </ConstructorLayout>
  );
}
