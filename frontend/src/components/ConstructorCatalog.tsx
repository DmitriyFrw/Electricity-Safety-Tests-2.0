import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { axiosErrorMessage } from "../api/getReact";
import { SAFETY_GROUPS, safetyGroupLabel } from "../constants/safetyGroups";
import type { TestListItem } from "../types/api";

type TabId = "all" | "drafts" | "archive";
type SortKey = "title" | "author";

const QUESTIONS_PER_TICKET = 10;
const PAGE_SIZES = [10, 20, 50] as const;

const TOPIC_PILL: Record<string, string> = {
  I: "constructor-topic--yellow",
  II: "constructor-topic--purple",
  III: "constructor-topic--mint",
  IV: "constructor-topic--blue",
};

function topicClass(group: string): string {
  return TOPIC_PILL[group] ?? "constructor-topic--gray";
}

function questionCount(test: TestListItem): number {
  return test.ticket_count * QUESTIONS_PER_TICKET;
}

function statusMeta(test: TestListItem): { label: string; className: string } {
  if (test.ticket_count === 0) {
    return { label: "Архив", className: "constructor-status--archive" };
  }
  if (test.published && test.content_complete) {
    return { label: "Опубликован", className: "constructor-status--published" };
  }
  if (test.published) {
    return { label: "Не заполнен", className: "constructor-status--draft" };
  }
  if (test.content_complete) {
    return { label: "К публикации", className: "constructor-status--ready" };
  }
  return { label: "Черновик", className: "constructor-status--draft" };
}

type Props = {
  onCreateClick?: () => void;
};

export default function ConstructorCatalog({ onCreateClick }: Props) {
  const navigate = useNavigate();
  const [tests, setTests] = useState<TestListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [tab, setTab] = useState<TabId>("all");
  const [search, setSearch] = useState("");
  const [topicFilter, setTopicFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortKey, setSortKey] = useState<SortKey>("title");
  const [sortAsc, setSortAsc] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState<(typeof PAGE_SIZES)[number]>(10);
  const [selected, setSelected] = useState<Set<number>>(new Set());

  useEffect(() => {
    void (async () => {
      setLoading(true);
      setError("");
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

  const filtered = useMemo(() => {
    let rows = [...tests];
    const q = search.trim().toLowerCase();
    if (q) {
      rows = rows.filter(
        (t) =>
          t.title.toLowerCase().includes(q) ||
          (t.description ?? "").toLowerCase().includes(q)
      );
    }
    if (topicFilter !== "all") {
      rows = rows.filter((t) => t.safety_group === topicFilter);
    }
    if (statusFilter === "published") {
      rows = rows.filter((t) => t.published && t.content_complete);
    } else if (statusFilter === "draft") {
      rows = rows.filter((t) => !t.published && t.ticket_count > 0);
    } else if (statusFilter === "archive") {
      rows = rows.filter((t) => t.ticket_count === 0);
    }
    if (tab === "drafts") {
      rows = rows.filter((t) => !t.published && t.ticket_count > 0);
    } else if (tab === "archive") {
      rows = rows.filter((t) => t.ticket_count === 0);
    }
    rows.sort((a, b) => {
      const av = sortKey === "title" ? a.title : a.author_username;
      const bv = sortKey === "title" ? b.title : b.author_username;
      const cmp = av.localeCompare(bv, "ru", { sensitivity: "base" });
      return sortAsc ? cmp : -cmp;
    });
    return rows;
  }, [tests, search, topicFilter, statusFilter, tab, sortKey, sortAsc]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const pageRows = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const rangeStart = filtered.length === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const rangeEnd = Math.min(currentPage * pageSize, filtered.length);

  useEffect(() => {
    setPage(1);
  }, [search, topicFilter, statusFilter, tab, pageSize]);

  const toggleAll = () => {
    if (pageRows.every((r) => selected.has(r.id))) {
      setSelected((prev) => {
        const next = new Set(prev);
        pageRows.forEach((r) => next.delete(r.id));
        return next;
      });
    } else {
      setSelected((prev) => {
        const next = new Set(prev);
        pageRows.forEach((r) => next.add(r.id));
        return next;
      });
    }
  };

  const onDelete = async (test: TestListItem) => {
    const ok = window.confirm(
      `Удалить «${test.title}»? Билеты и вопросы будут удалены без возможности восстановления.`
    );
    if (!ok) return;
    setDeletingId(test.id);
    setError("");
    try {
      await api.deleteTest(test.id);
      setTests((prev) => prev.filter((t) => t.id !== test.id));
      setSelected((prev) => {
        const next = new Set(prev);
        next.delete(test.id);
        return next;
      });
    } catch (e) {
      setError(axiosErrorMessage(e));
    } finally {
      setDeletingId(null);
    }
  };

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc((v) => !v);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  };

  return (
    <div className="constructor-catalog">
      <div className="constructor-catalog__tabs" role="tablist" aria-label="Фильтр билетов">
        {(
          [
            ["all", "Все билеты"],
            ["drafts", "Черновики"],
            ["archive", "Архив"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            className={`constructor-catalog__tab${tab === id ? " constructor-catalog__tab--active" : ""}`}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="constructor-catalog__toolbar">
        <label className="constructor-catalog__search">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
            <circle cx="11" cy="11" r="7" />
            <path d="M20 20l-3.5-3.5" />
          </svg>
          <input
            type="search"
            placeholder="Поиск по названию или описанию"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <label className="constructor-catalog__filter">
          <span>Тема</span>
          <select value={topicFilter} onChange={(e) => setTopicFilter(e.target.value)}>
            <option value="all">Все темы</option>
            {SAFETY_GROUPS.map((g) => (
              <option key={g.id} value={g.id}>
                {g.label}
              </option>
            ))}
          </select>
        </label>
        <label className="constructor-catalog__filter">
          <span>Статус</span>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">Все статусы</option>
            <option value="published">Опубликован</option>
            <option value="draft">Черновик</option>
            <option value="archive">Архив</option>
          </select>
        </label>
        <button type="button" className="constructor-catalog__filters-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
            <path d="M4 6h16M7 12h10M10 18h4" />
          </svg>
          Фильтры
        </button>
      </div>

      {error && <p className="auth-error constructor-catalog__error">{error}</p>}

      <div className="constructor-catalog__table-wrap">
        <table className="constructor-catalog__table">
          <thead>
            <tr>
              <th className="constructor-catalog__check-col">
                <input
                  type="checkbox"
                  aria-label="Выбрать все на странице"
                  checked={pageRows.length > 0 && pageRows.every((r) => selected.has(r.id))}
                  onChange={toggleAll}
                />
              </th>
              <th>
                <button type="button" className="constructor-catalog__sort" onClick={() => toggleSort("title")}>
                  Название билета
                  {sortKey === "title" && <span aria-hidden>{sortAsc ? " ↓" : " ↑"}</span>}
                </button>
              </th>
              <th>Тема</th>
              <th>Вопросов</th>
              <th>Статус</th>
              <th>
                <button type="button" className="constructor-catalog__sort" onClick={() => toggleSort("author")}>
                  Обновлён
                  {sortKey === "author" && <span aria-hidden>{sortAsc ? " ↓" : " ↑"}</span>}
                </button>
              </th>
              <th className="constructor-catalog__actions-col">Действия</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="constructor-catalog__empty">
                  Загрузка…
                </td>
              </tr>
            ) : pageRows.length === 0 ? (
              <tr>
                <td colSpan={7} className="constructor-catalog__empty">
                  {tests.length === 0 ? (
                    <>
                      Нет доступных билетов.{" "}
                      <button
                        type="button"
                        className="mockup-link mockup-link--btn"
                        onClick={onCreateClick}
                      >
                        Создать тест
                      </button>
                    </>
                  ) : (
                    "Ничего не найдено"
                  )}
                </td>
              </tr>
            ) : (
              pageRows.map((test) => {
                const status = statusMeta(test);
                return (
                  <tr key={test.id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selected.has(test.id)}
                        aria-label={`Выбрать ${test.title}`}
                        onChange={() =>
                          setSelected((prev) => {
                            const next = new Set(prev);
                            if (next.has(test.id)) next.delete(test.id);
                            else next.add(test.id);
                            return next;
                          })
                        }
                      />
                    </td>
                    <td>
                      <button
                        type="button"
                        className="constructor-catalog__name-btn"
                        onClick={() => navigate(`/constructor/${test.id}`)}
                      >
                        <strong>{test.title}</strong>
                        {test.description && (
                          <span className="constructor-catalog__desc">{test.description}</span>
                        )}
                      </button>
                    </td>
                    <td>
                      <span className={`constructor-topic ${topicClass(test.safety_group)}`}>
                        {safetyGroupLabel(test.safety_group)}
                      </span>
                    </td>
                    <td>{questionCount(test)}</td>
                    <td>
                      <span className={`constructor-status ${status.className}`}>{status.label}</span>
                    </td>
                    <td>
                      <span className="constructor-catalog__updated">{test.author_username}</span>
                    </td>
                    <td>
                      <div className="constructor-catalog__row-actions">
                        <button
                          type="button"
                          className="constructor-catalog__edit"
                          title="Редактировать"
                          aria-label={`Редактировать ${test.title}`}
                          onClick={() => navigate(`/constructor/${test.id}`)}
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
                            <path d="M12 20h9" />
                            <path d="M16.5 3.5a2.12 2.12 0 013 3L7 19l-4 1 1-4 12.5-12.5z" />
                          </svg>
                        </button>
                        <button
                          type="button"
                          className="constructor-catalog__more"
                          title="Удалить"
                          aria-label={`Удалить ${test.title}`}
                          disabled={deletingId === test.id}
                          onClick={() => void onDelete(test)}
                        >
                          ⋯
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <footer className="constructor-catalog__footer">
        <span className="constructor-catalog__range">
          Показано {rangeStart}–{rangeEnd} из {filtered.length}
        </span>
        <div className="constructor-catalog__pagination">
          <button
            type="button"
            disabled={currentPage <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            aria-label="Предыдущая страница"
          >
            ‹
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter((n) => n === 1 || n === totalPages || Math.abs(n - currentPage) <= 1)
            .map((n, idx, arr) => {
              const prev = arr[idx - 1];
              const showGap = prev != null && n - prev > 1;
              return (
                <span key={n} className="constructor-catalog__page-group">
                  {showGap && <span className="constructor-catalog__page-gap">…</span>}
                  <button
                    type="button"
                    className={n === currentPage ? "constructor-catalog__page--active" : ""}
                    onClick={() => setPage(n)}
                  >
                    {n}
                  </button>
                </span>
              );
            })}
          <button
            type="button"
            disabled={currentPage >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            aria-label="Следующая страница"
          >
            ›
          </button>
        </div>
        <label className="constructor-catalog__page-size">
          На странице:
          <select
            value={pageSize}
            onChange={(e) => setPageSize(Number(e.target.value) as (typeof PAGE_SIZES)[number])}
          >
            {PAGE_SIZES.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
      </footer>
    </div>
  );
}
