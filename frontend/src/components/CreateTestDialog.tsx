import { FormEvent, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { axiosErrorMessage } from "../api/getReact";
import { SAFETY_GROUPS } from "../constants/safetyGroups";

type Props = {
  open: boolean;
  onClose: () => void;
};

export default function CreateTestDialog({ open, onClose }: Props) {
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    setError("");
    setLoading(false);
    const t = window.setTimeout(() => titleRef.current?.focus(), 0);
    return () => window.clearTimeout(t);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const fd = new FormData(e.target as HTMLFormElement);
    setLoading(true);
    setError("");
    try {
      const t = await api.createTest(
        String(fd.get("title")),
        String(fd.get("description") || ""),
        String(fd.get("safety_group") || "II")
      );
      onClose();
      navigate(`/constructor/${t.id}`);
    } catch (err) {
      setError(axiosErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="constructor-dialog-backdrop" onClick={onClose} role="presentation">
      <div
        className="constructor-dialog mockup-page-card mockup-form-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-test-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="mockup-page-header">
          <h2 id="create-test-title">Новый тест</h2>
        </header>
        {error && <p className="auth-error">{error}</p>}
        <form className="mockup-form" onSubmit={onSubmit}>
          <label htmlFor="create-test-title-input">Название</label>
          <input
            ref={titleRef}
            id="create-test-title-input"
            name="title"
            className="mockup-input"
            required
            maxLength={200}
            disabled={loading}
          />
          <label htmlFor="create-test-description">Описание</label>
          <textarea
            id="create-test-description"
            name="description"
            className="mockup-input"
            rows={4}
            disabled={loading}
          />
          <label htmlFor="create-test-safety-group">Группа по электробезопасности</label>
          <select
            id="create-test-safety-group"
            name="safety_group"
            className="mockup-select"
            defaultValue="II"
            disabled={loading}
          >
            {SAFETY_GROUPS.map((g) => (
              <option key={g.id} value={g.id}>
                {g.label}
              </option>
            ))}
          </select>
          <div className="mockup-form__actions">
            <button type="submit" className="mockup-btn mockup-btn--primary" disabled={loading}>
              {loading ? "Создание…" : "Создать"}
            </button>
            <button
              type="button"
              className="mockup-btn mockup-btn--outline"
              disabled={loading}
              onClick={onClose}
            >
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
