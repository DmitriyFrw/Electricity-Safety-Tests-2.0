import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { axiosErrorMessage } from "../api/getReact";
import { SAFETY_GROUPS } from "../constants/safetyGroups";
import DashboardLayout from "../layout/DashboardLayout";

export default function TestNewPage() {
  const navigate = useNavigate();
  const [error, setError] = useState("");

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const fd = new FormData(e.target as HTMLFormElement);
    try {
      const t = await api.createTest(
        String(fd.get("title")),
        String(fd.get("description") || ""),
        String(fd.get("safety_group") || "II")
      );
      navigate(`/constructor/${t.id}`);
    } catch (err) {
      setError(axiosErrorMessage(err));
    }
  };

  return (
    <DashboardLayout active="constructor">
      <div className="dash-page-card dash-form">
        <h1>Новый тест</h1>
        {error && <p className="auth-error">{error}</p>}
        <form onSubmit={onSubmit}>
          <label htmlFor="title">Название</label>
          <input id="title" name="title" required maxLength={200} />
          <label htmlFor="description">Описание</label>
          <textarea id="description" name="description" />
          <label htmlFor="safety_group">Группа по электробезопасности</label>
          <select id="safety_group" name="safety_group" defaultValue="II">
            {SAFETY_GROUPS.map((g) => (
              <option key={g.id} value={g.id}>
                {g.label}
              </option>
            ))}
          </select>
          <button type="submit" className="dash-exam-btn" style={{ border: "none", cursor: "pointer", marginTop: "1rem" }}>
            Создать
          </button>
          <Link to="/cabinet" className="dash-card-link" style={{ marginLeft: "1rem" }}>
            Отмена
          </Link>
        </form>
      </div>
    </DashboardLayout>
  );
}
