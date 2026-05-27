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
        if (!res.ok) throw new Error("Не удалось загрузить мануал");
        setContent(await res.text());
      } catch (e) {
        setContent("");
        setError(e instanceof Error ? e.message : "Ошибка");
      }
    })();
  }, [activeId]);

  return (
    <DashboardLayout active="manuals">
      <div className="dash-page-card">
        <h1>Мануалы</h1>
        <p className="dash-card-note">Справочные материалы по электробезопасности</p>
      </div>
      {error && <p className="auth-error">{error}</p>}
      {loading && <p className="dash-card-note">Загрузка…</p>}
      {!loading && manuals.length === 0 && (
        <p className="dash-card-note">Мануалы пока не добавлены.</p>
      )}
      {manuals.length > 0 && (
        <div className="dash-manuals-layout">
          <aside className="dash-manuals-list">
            {manuals.map((m) => (
              <button
                key={m.id}
                type="button"
                className={`dash-manuals-item ${activeId === m.id ? "is-active" : ""}`}
                onClick={() => setActiveId(m.id)}
              >
                {m.title}
              </button>
            ))}
          </aside>
          <article className="dash-page-card dash-manuals-content">
            <pre className="dash-manual-text">{content}</pre>
          </article>
        </div>
      )}
      <p className="dash-card-meta">
        <Link to="/cabinet">← В личный кабинет</Link>
      </p>
    </DashboardLayout>
  );
}
