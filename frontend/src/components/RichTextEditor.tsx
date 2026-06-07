import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

const FONTS = [
  { label: "Arial", value: "Arial, sans-serif" },
  { label: "Times New Roman", value: '"Times New Roman", serif' },
  { label: "Georgia", value: "Georgia, serif" },
  { label: "Courier New", value: '"Courier New", monospace' },
] as const;

const SIZES = ["12px", "14px", "16px", "18px", "20px", "24px", "28px"] as const;

const TEXT_COLORS = ["#111827", "#E85D5D", "#2563EB", "#059669", "#D97706", "#7C3AED"] as const;

const HIGHLIGHT_COLORS = ["#FEF08A", "#BBF7D0", "#BFDBFE", "#FECACA", "#E9D5FF", "#FFFFFF"] as const;

const BLOCK_STYLES = [
  { label: "Обычный", value: "p" },
  { label: "Подзаголовок", value: "h4" },
  { label: "Заголовок", value: "h3" },
] as const;

type Props = {
  label: string;
  value: string;
  onChange: (html: string) => void;
  minHeight?: number;
  gridLayout?: boolean;
  enableLinks?: boolean;
};

function applyCommand(cmd: string, value?: string) {
  document.execCommand(cmd, false, value);
}

function focusEditor(ref: React.RefObject<HTMLDivElement | null>) {
  ref.current?.focus();
}

function ToolbarBtn({
  title,
  onClick,
  children,
  active,
}: {
  title: string;
  onClick: () => void;
  children: ReactNode;
  active?: boolean;
}) {
  return (
    <button
      type="button"
      className={`rich-editor-btn${active ? " rich-editor-btn-active" : ""}`}
      title={title}
      onMouseDown={(e) => e.preventDefault()}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

function ColorPopup({
  open,
  onClose,
  colors,
  ariaLabel,
  onPick,
  wrapRef,
}: {
  open: boolean;
  onClose: () => void;
  colors: readonly string[];
  ariaLabel: string;
  onPick: (c: string) => void;
  wrapRef: React.RefObject<HTMLDivElement | null>;
}) {
  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open, onClose, wrapRef]);

  if (!open) return null;
  return (
    <div className="rich-editor-color-popup" role="menu" aria-label={ariaLabel}>
      <div className="rich-editor-color-grid">
        {colors.map((c) => (
          <button
            key={c}
            type="button"
            role="menuitem"
            className="rich-editor-color-tile"
            title={c}
            style={{ background: c }}
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => onPick(c)}
          />
        ))}
      </div>
    </div>
  );
}

function FormatToolbar({
  run,
  onFont,
  onSize,
  onBlockStyle,
  colorWrapRef,
  highlightWrapRef,
  colorOpen,
  setColorOpen,
  highlightOpen,
  setHighlightOpen,
  enableLinks,
}: {
  run: (cmd: string, val?: string) => void;
  onFont: (family: string) => void;
  onSize: (size: string) => void;
  onBlockStyle: (tag: string) => void;
  colorWrapRef: React.RefObject<HTMLDivElement | null>;
  highlightWrapRef: React.RefObject<HTMLDivElement | null>;
  colorOpen: boolean;
  setColorOpen: (v: boolean | ((prev: boolean) => boolean)) => void;
  highlightOpen: boolean;
  setHighlightOpen: (v: boolean | ((prev: boolean) => boolean)) => void;
  enableLinks?: boolean;
}) {
  return (
    <div className="rich-editor-toolbar" role="toolbar" aria-label="Инструменты форматирования">
      <div className="rich-editor-toolbar-row">
        <div className="rich-editor-group">
          <ToolbarBtn title="Отменить (Ctrl+Z)" onClick={() => run("undo")}>
            <span className="rte-glyph rte-glyph-undo" aria-hidden />
          </ToolbarBtn>
          <ToolbarBtn title="Повторить (Ctrl+Y)" onClick={() => run("redo")}>
            <span className="rte-glyph rte-glyph-redo" aria-hidden />
          </ToolbarBtn>
        </div>
        <div className="rich-editor-group">
          <ToolbarBtn title="Жирный (Ctrl+B)" onClick={() => run("bold")}>
            <span className="rte-label rte-label-bold">B</span>
          </ToolbarBtn>
          <ToolbarBtn title="Курсив (Ctrl+I)" onClick={() => run("italic")}>
            <span className="rte-label rte-label-italic">I</span>
          </ToolbarBtn>
          <ToolbarBtn title="Подчёркивание (Ctrl+U)" onClick={() => run("underline")}>
            <span className="rte-label rte-label-underline">U</span>
          </ToolbarBtn>
          <ToolbarBtn title="Зачёркнутый" onClick={() => run("strikeThrough")}>
            <span className="rte-label rte-label-strike">S</span>
          </ToolbarBtn>
        </div>
        <div className="rich-editor-group rich-editor-color-wrap" ref={colorWrapRef as React.Ref<HTMLDivElement>}>
          <ToolbarBtn
            title="Цвет текста"
            onClick={() => {
              setHighlightOpen(false);
              setColorOpen((v) => !v);
            }}
          >
            <span className="rich-editor-color-trigger-icon">A</span>
          </ToolbarBtn>
          <ColorPopup
            open={colorOpen}
            onClose={() => setColorOpen(false)}
            colors={TEXT_COLORS}
            ariaLabel="Цвет текста"
            wrapRef={colorWrapRef}
            onPick={(c) => {
              run("foreColor", c);
              setColorOpen(false);
            }}
          />
        </div>
        <div className="rich-editor-group rich-editor-color-wrap" ref={highlightWrapRef as React.Ref<HTMLDivElement>}>
          <ToolbarBtn
            title="Цвет фона"
            onClick={() => {
              setColorOpen(false);
              setHighlightOpen((v) => !v);
            }}
          >
            <span className="rich-editor-highlight-icon">▮</span>
          </ToolbarBtn>
          <ColorPopup
            open={highlightOpen}
            onClose={() => setHighlightOpen(false)}
            colors={HIGHLIGHT_COLORS}
            ariaLabel="Цвет выделения"
            wrapRef={highlightWrapRef}
            onPick={(c) => {
              run("hiliteColor", c);
              setHighlightOpen(false);
            }}
          />
        </div>
      </div>

      <div className="rich-editor-toolbar-row">
        <div className="rich-editor-group">
          <select
            className="rich-editor-select"
            aria-label="Стиль абзаца"
            defaultValue=""
            onChange={(e) => {
              if (e.target.value) onBlockStyle(e.target.value);
              e.target.value = "";
            }}
          >
            <option value="">Стиль</option>
            {BLOCK_STYLES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
          <select
            className="rich-editor-select"
            aria-label="Шрифт"
            defaultValue=""
            onChange={(e) => {
              if (e.target.value) onFont(e.target.value);
              e.target.value = "";
            }}
          >
            <option value="">Шрифт</option>
            {FONTS.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label}
              </option>
            ))}
          </select>
          <select
            className="rich-editor-select"
            aria-label="Размер"
            defaultValue=""
            onChange={(e) => {
              if (e.target.value) onSize(e.target.value);
              e.target.value = "";
            }}
          >
            <option value="">Размер</option>
            {SIZES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="rich-editor-group">
          <ToolbarBtn title="По левому краю" onClick={() => run("justifyLeft")}>
            <span className="rte-glyph rte-glyph-align-left" aria-hidden />
          </ToolbarBtn>
          <ToolbarBtn title="По центру" onClick={() => run("justifyCenter")}>
            <span className="rte-glyph rte-glyph-align-center" aria-hidden />
          </ToolbarBtn>
          <ToolbarBtn title="По правому краю" onClick={() => run("justifyRight")}>
            <span className="rte-glyph rte-glyph-align-right" aria-hidden />
          </ToolbarBtn>
        </div>
        <div className="rich-editor-group">
          <ToolbarBtn title="Маркированный список" onClick={() => run("insertUnorderedList")}>
            <span className="rte-glyph rte-glyph-list-bullet" aria-hidden />
          </ToolbarBtn>
          <ToolbarBtn title="Нумерованный список" onClick={() => run("insertOrderedList")}>
            <span className="rte-glyph rte-glyph-list-number" aria-hidden />
          </ToolbarBtn>
        </div>
        <div className="rich-editor-group">
          <ToolbarBtn title="Убрать форматирование" onClick={() => run("removeFormat")}>
            <span className="rte-glyph rte-glyph-clear" aria-hidden />
          </ToolbarBtn>
        </div>
        {enableLinks && (
          <div className="rich-editor-group">
            <ToolbarBtn title="Вставить ссылку" onClick={() => run("createLinkPrompt")}>
              <span className="rte-glyph rte-glyph-link" aria-hidden />
            </ToolbarBtn>
            <ToolbarBtn title="Убрать ссылку" onClick={() => run("unlink")}>
              <span className="rte-label">⌫</span>
            </ToolbarBtn>
          </div>
        )}
      </div>
    </div>
  );
}

export default function RichTextEditor({
  label,
  value,
  onChange,
  minHeight = 88,
  gridLayout = false,
  enableLinks = false,
}: Props) {
  const editorRef = useRef<HTMLDivElement>(null);
  const colorWrapRef = useRef<HTMLDivElement>(null);
  const highlightWrapRef = useRef<HTMLDivElement>(null);
  const [colorOpen, setColorOpen] = useState(false);
  const [highlightOpen, setHighlightOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const sync = useCallback(() => {
    const el = editorRef.current;
    if (!el) return;
    onChange(el.innerHTML);
  }, [onChange]);

  const run = useCallback(
    (cmd: string, val?: string) => {
      focusEditor(editorRef);
      if (cmd === "createLinkPrompt") {
        const selected = window.getSelection()?.toString() ?? "";
        let url = window.prompt("Адрес ссылки", "https://");
        if (!url) return;
        url = url.trim();
        if (!/^https?:\/\//i.test(url) && !url.startsWith("/")) {
          url = `https://${url}`;
        }
        if (selected) {
          applyCommand("createLink", url);
        } else {
          const text = window.prompt("Текст ссылки", url) || url;
          applyCommand(
            "insertHTML",
            `<a href="${url.replace(/"/g, "&quot;")}" target="_blank" rel="noopener noreferrer">${text.replace(/</g, "&lt;")}</a>`
          );
        }
      } else {
        applyCommand(cmd, val);
      }
      sync();
    },
    [sync]
  );

  useEffect(() => {
    const el = editorRef.current;
    if (!el) return;
    if (el.innerHTML !== value) {
      el.innerHTML = value || "";
    }
  }, [value]);

  const onFont = (family: string) => {
    focusEditor(editorRef);
    applyCommand("fontName", family);
    sync();
  };

  const onSize = (size: string) => {
    focusEditor(editorRef);
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
      sync();
      return;
    }
    const range = selection.getRangeAt(0);
    if (range.collapsed) {
      applyCommand("insertHTML", `<span style="font-size:${size}">&#8203;</span>`);
    } else {
      const span = document.createElement("span");
      span.style.fontSize = size;
      try {
        range.surroundContents(span);
      } catch {
        applyCommand("fontSize", "4");
      }
    }
    sync();
  };

  const onBlockStyle = (tag: string) => {
    focusEditor(editorRef);
    applyCommand("formatBlock", tag === "p" ? "p" : tag);
    sync();
  };

  useEffect(() => {
    const el = editorRef.current;
    if (!el) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey)) return;
      const key = e.key.toLowerCase();
      if (key === "b") {
        e.preventDefault();
        run("bold");
      } else if (key === "i") {
        e.preventDefault();
        run("italic");
      } else if (key === "u") {
        e.preventDefault();
        run("underline");
      } else if (key === "z" && !e.shiftKey) {
        e.preventDefault();
        run("undo");
      } else if ((key === "z" && e.shiftKey) || key === "y") {
        e.preventDefault();
        run("redo");
      }
    };
    el.addEventListener("keydown", onKeyDown);
    return () => el.removeEventListener("keydown", onKeyDown);
  }, [run]);

  return (
    <div className="rich-editor">
      <label className="rich-editor-label">{label}</label>
      <div className="rich-editor-panel">
        <details
          className="rich-editor-format-menu"
          open={menuOpen}
          onToggle={(e) => setMenuOpen((e.target as HTMLDetailsElement).open)}
        >
          <summary className="rich-editor-format-summary">Форматирование</summary>
          <FormatToolbar
            run={run}
            onFont={onFont}
            onSize={onSize}
            onBlockStyle={onBlockStyle}
            colorWrapRef={colorWrapRef}
            highlightWrapRef={highlightWrapRef}
            colorOpen={colorOpen}
            setColorOpen={setColorOpen}
            highlightOpen={highlightOpen}
            setHighlightOpen={setHighlightOpen}
            enableLinks={enableLinks}
          />
        </details>
        <div
          ref={editorRef}
          className={`rich-editor-area${gridLayout ? " rich-editor-area-grid" : ""}`}
          contentEditable
          role="textbox"
          aria-label={label}
          data-placeholder="Введите текст…"
          style={{ minHeight }}
          onInput={sync}
          onBlur={sync}
          onFocus={() => {
            setColorOpen(false);
            setHighlightOpen(false);
          }}
          suppressContentEditableWarning
        />
      </div>
    </div>
  );
}
