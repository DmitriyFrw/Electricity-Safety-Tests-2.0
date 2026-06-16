import { ChangeEvent, useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { axiosErrorMessage } from "../api/getReact";
import RichHtml from "../components/RichHtml";
import RichTextEditor from "../components/RichTextEditor";
import TopNavLayout from "../layout/TopNavLayout";
import { useAuth } from "../auth/AuthContext";
import type { WikiAttachment, WikiPage, WikiPageListItem } from "../types/api";

const wikiMascot = "/razvivaisia/assets/images/wiki-mascot.png";

function formatBytes(n: number): string {
  if (n < 1024) return `${n} Б`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} КБ`;
  return `${(n / (1024 * 1024)).toFixed(1)} МБ`;
}

function WikiPageContent({ page }: { page: WikiPage }) {
  const inlineAttachments = page.attachments.filter(
    (a) => !page.content.includes(a.url)
  );

  return (
    <div className="wiki-page-content">
      {page.content.trim() ? (
        <RichHtml html={page.content} className="rich-html wiki-rich-html" />
      ) : (
        <p className="dash-card-note">Содержимое страницы пока пустое.</p>
      )}
      {inlineAttachments.length > 0 && (
        <div className="wiki-page-files">
          <div className="wiki-page-files-title">Файлы</div>
          <ul className="wiki-page-files-list">
            {inlineAttachments.map((att) => (
              <WikiAttachmentItem key={att.id} att={att} />
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function WikiAttachmentItem({ att, onDelete }: { att: WikiAttachment; onDelete?: () => void }) {
  if (att.is_image) {
    return (
      <li className="wiki-page-file wiki-page-file-image">
        <img src={att.url} alt={att.filename} className="wiki-page-inline-image" />
        <div className="wiki-page-file-meta">
          <a href={att.url} className="dash-card-link" download={att.filename}>
            {att.filename}
          </a>
          <span className="dash-card-note"> · {formatBytes(att.size_bytes)}</span>
          {onDelete && (
            <button type="button" className="btn btn-sm btn-outline wiki-page-file-delete" onClick={onDelete}>
              Удалить
            </button>
          )}
        </div>
      </li>
    );
  }

  return (
    <li className="wiki-page-file">
      <a href={att.url} className="dash-card-link" download={att.filename}>
        {att.filename}
      </a>
      <span className="dash-card-note"> · {formatBytes(att.size_bytes)}</span>
      {onDelete && (
        <button type="button" className="btn btn-sm btn-outline wiki-page-file-delete" onClick={onDelete}>
          Удалить
        </button>
      )}
    </li>
  );
}

type EditorMode = { kind: "create" } | { kind: "edit"; pageId: number };

function WikiEditor({
  mode,
  initialTitle,
  initialContent,
  initialAttachments,
  onSaved,
  onCancel,
  onDeleted,
}: {
  mode: EditorMode;
  initialTitle: string;
  initialContent: string;
  initialAttachments: WikiAttachment[];
  onSaved: (page: WikiPage) => void;
  onCancel: () => void;
  onDeleted?: () => void;
}) {
  const [title, setTitle] = useState(initialTitle);
  const [content, setContent] = useState(initialContent);
  const [attachments, setAttachments] = useState(initialAttachments);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const pageIdRef = useRef<number | null>(mode.kind === "edit" ? mode.pageId : null);

  const ensurePageId = useCallback(async (): Promise<number> => {
    if (pageIdRef.current != null) return pageIdRef.current;
    const trimmed = title.trim();
    if (!trimmed) throw new Error("Укажите название страницы");
    const created = await api.createWikiPage(trimmed, content);
    pageIdRef.current = created.id;
    setAttachments(created.attachments);
    return created.id;
  }, [title, content]);

  const onPickFiles = async (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files?.length) return;
    setError("");
    setUploading(true);
    try {
      const pageId = await ensurePageId();
      for (const file of Array.from(files)) {
        const att = await api.uploadWikiAttachment(pageId, file);
        setAttachments((prev) => [...prev, att]);
        if (file.type.startsWith("image/")) {
          setContent(
            (prev) =>
              `${prev}${prev ? "<p><br></p>" : ""}<p><img src="${att.url}" alt="${file.name.replace(/"/g, "&quot;")}"></p>`
          );
        }
      }
    } catch (err) {
      setError(axiosErrorMessage(err));
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const onSave = async () => {
    setError("");
    const trimmed = title.trim();
    if (!trimmed) {
      setError("Укажите название страницы");
      return;
    }
    setSaving(true);
    try {
      let page: WikiPage;
      if (mode.kind === "create" && pageIdRef.current == null) {
        page = await api.createWikiPage(trimmed, content);
      } else {
        const pageId = pageIdRef.current ?? (mode.kind === "edit" ? mode.pageId : null);
        if (pageId == null) {
          page = await api.createWikiPage(trimmed, content);
        } else {
          page = await api.updateWikiPage(pageId, trimmed, content);
        }
      }
      onSaved(page);
    } catch (err) {
      setError(axiosErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const onDeletePage = async () => {
    if (mode.kind !== "edit" || !window.confirm("Удалить страницу?")) return;
    setSaving(true);
    setError("");
    try {
      await api.deleteWikiPage(mode.pageId);
      onDeleted?.();
    } catch (err) {
      setError(axiosErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const onDeleteAttachment = async (att: WikiAttachment) => {
    if (!window.confirm(`Удалить файл «${att.filename}»?`)) return;
    setUploading(true);
    setError("");
    try {
      const page = await api.deleteWikiAttachment(att.id);
      setAttachments(page.attachments);
      setContent(page.content);
    } catch (err) {
      setError(axiosErrorMessage(err));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="wiki-page-editor">
      <h2 className="wiki-page-editor-title">
        {mode.kind === "create" ? "Новая страница" : "Редактирование страницы"}
      </h2>
      {error && <p className="auth-error">{error}</p>}
      <label className="wiki-page-editor-label" htmlFor="wiki-page-title">
        Название страницы
      </label>
      <input
        id="wiki-page-title"
        className="wiki-page-editor-title-input"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        maxLength={200}
        required
      />
      <RichTextEditor
        label="Содержимое"
        value={content}
        onChange={setContent}
        minHeight={240}
        gridLayout
        enableLinks
      />
      <div className="wiki-page-editor-files">
        <input
          ref={fileRef}
          type="file"
          multiple
          accept="image/jpeg,image/png,image/gif,image/webp,.jpg,.jpeg,.png,.pdf,.doc,.docx,.txt"
          className="wiki-page-file-input"
          onChange={(e) => void onPickFiles(e)}
        />
        <button
          type="button"
          className="btn btn-outline btn-sm"
          disabled={uploading || saving}
          onClick={() => fileRef.current?.click()}
        >
          {uploading ? "Загрузка…" : "Прикрепить файл или изображение"}
        </button>
        {attachments.length > 0 && (
          <ul className="wiki-page-files-list wiki-page-editor-attachments">
            {attachments.map((att) => (
              <WikiAttachmentItem
                key={att.id}
                att={att}
                onDelete={() => void onDeleteAttachment(att)}
              />
            ))}
          </ul>
        )}
      </div>
      <div className="wiki-page-editor-actions">
        <button type="button" className="btn btn-primary" disabled={saving || uploading} onClick={() => void onSave()}>
          {saving ? "Сохранение…" : "Сохранить"}
        </button>
        <button type="button" className="btn btn-outline" disabled={saving || uploading} onClick={onCancel}>
          Отмена
        </button>
        {mode.kind === "edit" && (
          <button type="button" className="btn btn-outline wiki-page-delete-btn" disabled={saving} onClick={() => void onDeletePage()}>
            Удалить страницу
          </button>
        )}
      </div>
    </div>
  );
}

function WikiAccordionItem({
  item,
  expanded,
  onToggle,
  canEdit,
  page,
  loading,
  onEdit,
}: {
  item: WikiPageListItem;
  expanded: boolean;
  onToggle: () => void;
  canEdit: boolean;
  page: WikiPage | null;
  loading: boolean;
  onEdit: () => void;
}) {
  return (
    <div className={`wiki-accordion-item${expanded ? " wiki-accordion-item-open" : ""}`}>
      <div className="wiki-accordion-header">
        <button type="button" className="wiki-accordion-title" onClick={onToggle} aria-expanded={expanded}>
          <span className="wiki-accordion-chevron" aria-hidden />
          {item.title}
        </button>
        {canEdit && expanded && (
          <button type="button" className="btn btn-sm btn-outline" onClick={onEdit}>
            Редактировать
          </button>
        )}
      </div>
      {expanded && (
        <div className="wiki-accordion-body">
          {loading && <p className="dash-card-note">Загрузка…</p>}
          {!loading && page && <WikiPageContent page={page} />}
        </div>
      )}
    </div>
  );
}

export default function WikiPage() {
  const { user } = useAuth();
  const canEdit = user?.can_edit_wiki ?? false;
  const [pages, setPages] = useState<WikiPageListItem[]>([]);
  const [loaded, setLoaded] = useState<Record<number, WikiPage>>({});
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [loadingId, setLoadingId] = useState<number | null>(null);
  const [listError, setListError] = useState("");
  const [editorMode, setEditorMode] = useState<EditorMode | null>(null);

  const reloadList = useCallback(async () => {
    setListError("");
    try {
      const items = await api.listWikiPages();
      setPages(items);
    } catch (err) {
      setListError(axiosErrorMessage(err));
    }
  }, []);

  useEffect(() => {
    void reloadList();
  }, [reloadList]);

  useEffect(() => {
    if (editorMode?.kind === "edit") {
      void loadPage(editorMode.pageId);
    }
  }, [editorMode]);

  const loadPage = async (pageId: number) => {
    if (loaded[pageId]) return loaded[pageId];
    setLoadingId(pageId);
    try {
      const page = await api.getWikiPage(pageId);
      setLoaded((prev) => ({ ...prev, [pageId]: page }));
      return page;
    } finally {
      setLoadingId(null);
    }
  };

  const onToggle = (pageId: number) => {
    if (expandedId === pageId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(pageId);
    void loadPage(pageId);
  };

  const onEditorSaved = (page: WikiPage) => {
    setLoaded((prev) => ({ ...prev, [page.id]: page }));
    setPages((prev) => {
      const exists = prev.some((p) => p.id === page.id);
      if (exists) {
        return prev.map((p) => (p.id === page.id ? { ...p, title: page.title, updated_at: page.updated_at } : p));
      }
      return [...prev, { id: page.id, title: page.title, updated_at: page.updated_at }];
    });
    setEditorMode(null);
    setExpandedId(page.id);
  };

  const onEditorDeleted = (pageId: number) => {
    setPages((prev) => prev.filter((p) => p.id !== pageId));
    setLoaded((prev) => {
      const next = { ...prev };
      delete next[pageId];
      return next;
    });
    setEditorMode(null);
    if (expandedId === pageId) setExpandedId(null);
  };

  const editingPage =
    editorMode?.kind === "edit" ? loaded[editorMode.pageId] ?? null : null;

  return (
    <TopNavLayout>
      <div className="dash-page-card wiki-page">
        <Link to="/cabinet" className="dash-link-btn wiki-page-back">
          ← На главную
        </Link>

        <div className="wiki-page-hero">
          <img src={wikiMascot} alt="" className="wiki-page-mascot" />
          <div className="wiki-page-greeting">
            <h1 className="wiki-page-title">Привет!</h1>
            <p className="wiki-page-lead">
              Здесь ты найдешь всю актуальную информацию по работе сайта, его функционалу и работе.
            </p>
          </div>
        </div>

        {canEdit && !editorMode && (
          <div className="wiki-page-toolbar">
            <button type="button" className="btn btn-primary" onClick={() => setEditorMode({ kind: "create" })}>
              Создать страницу
            </button>
          </div>
        )}

        {editorMode?.kind === "create" && (
          <WikiEditor
            mode={editorMode}
            initialTitle=""
            initialContent=""
            initialAttachments={[]}
            onSaved={onEditorSaved}
            onCancel={() => setEditorMode(null)}
          />
        )}

        {editorMode?.kind === "edit" && !editingPage && (
          <p className="dash-card-note">Загрузка редактора…</p>
        )}

        {editorMode?.kind === "edit" && editingPage && (
          <WikiEditor
            mode={editorMode}
            initialTitle={editingPage.title}
            initialContent={editingPage.content}
            initialAttachments={editingPage.attachments}
            onSaved={onEditorSaved}
            onCancel={() => setEditorMode(null)}
            onDeleted={() => onEditorDeleted(editorMode.pageId)}
          />
        )}

        {listError && <p className="auth-error">{listError}</p>}

        <div className="wiki-accordion">
          {pages.length === 0 && !editorMode && (
            <p className="dash-card-note">Страниц пока нет{canEdit ? ". Нажмите «Создать страницу»." : "."}</p>
          )}
          {pages.map((item) => (
            <WikiAccordionItem
              key={item.id}
              item={item}
              expanded={expandedId === item.id}
              onToggle={() => onToggle(item.id)}
              canEdit={canEdit}
              page={loaded[item.id] ?? null}
              loading={loadingId === item.id}
              onEdit={() => {
                void loadPage(item.id).then(() => setEditorMode({ kind: "edit", pageId: item.id }));
              }}
            />
          ))}
        </div>
      </div>
    </TopNavLayout>
  );
}
