import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import DashboardLayout from "../layout/DashboardLayout";
import type { Manual } from "../types/api";

export default function ManualsPage() {
  const [manuals, setManuals] = useState<Manual[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const list = await api.listManuals();
        setManuals(list);
        if (list.length > 0) setActiveId(list[0].id);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Ошибка загрузки");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!activeId) return;
    (async () => {
      try {
        const res = await fetch(`/api/manuals/${activeId}`, { credentials: "include" });
        if (!res.ok) throw new Error("Не удалось загрузить документ");
        setContent(await res.text());
      } catch (e) {
        setContent("");
        setError(e instanceof Error ? e.message : "Ошибка");
      }
    })();
  }, [activeId]);

  return (
    <DashboardLayout active="manuals">
      <div className="documents-card">
        <h1>Нормативные документы</h1>
        <p className="dash-card-note">Справочные материалы для подготовки к экзамену</p>
        {error && <p className="auth-error">{error}</p>}
        {loading && <p className="dash-card-note">Загрузка…</p>}
        {!loading && manuals.length === 0 && <p className="dash-card-note">Документы пока не добавлены.</p>}
        {manuals.length > 0 && (
          <>
            <ul className="documents-list">
              {manuals.map((m) => (
                <li key={m.id}>
                  <button
                    type="button"
                    className={`documents-link ${activeId === m.id ? "active" : ""}`}
                    onClick={() => setActiveId(m.id)}
                  >
                    {m.title}
                  </button>
                </li>
              ))}
            </ul>
            <article className="documents-preview">
              <pre className="dash-manual-text">{content}</pre>
            </article>
          </>
        )}
        <p className="dash-card-meta" style={{ marginTop: "var(--spacing-4)" }}>
          <Link to="/cabinet">← В личный кабинет</Link>
        </p>
      </div>
    </DashboardLayout>
  );
}
