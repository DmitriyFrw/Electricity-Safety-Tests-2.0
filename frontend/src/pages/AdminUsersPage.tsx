import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { axiosErrorMessage } from "../api/getReact";
import { useAuth } from "../auth/AuthContext";
import { ASSIGNABLE_ROLES } from "../constants/roles";
import DashboardLayout from "../layout/DashboardLayout";
import type { UserAdmin } from "../types/api";

export default function AdminUsersPage() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<UserAdmin[]>([]);
  const [roles, setRoles] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [savingId, setSavingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const list = await api.listAdminUsers();
      setUsers(list);
      setRoles(Object.fromEntries(list.map((u) => [u.id, u.role])));
    } catch (err) {
      setError(axiosErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const onSaveRole = async (target: UserAdmin) => {
    const role = roles[target.id];
    if (!role || role === target.role) return;
    setSavingId(target.id);
    setMessage("");
    setError("");
    try {
      const updated = await api.updateUserRole(target.id, role);
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      setRoles((prev) => ({ ...prev, [updated.id]: updated.role }));
      setMessage(`Роль пользователя ${updated.username} обновлена`);
    } catch (err) {
      setError(axiosErrorMessage(err));
    } finally {
      setSavingId(null);
    }
  };

  return (
    <DashboardLayout active="admin">
      <h1 className="dash-section-title">Пользователи</h1>
      <p className="dash-card-note" style={{ marginBottom: "var(--spacing-4)" }}>
        Назначение ролей: администратор, Еж (редактор тестов), Кот (экзамен и протокол). Свою роль
        изменить нельзя.
      </p>
      {error && <p className="auth-error">{error}</p>}
      {message && <p className="dash-card-note">{message}</p>}
      {loading ? (
        <p className="dash-card-note">Загрузка…</p>
      ) : (
        <div className="dash-table-wrap">
          <table className="dash-table">
            <thead>
              <tr>
                <th>Логин</th>
                <th>Отображаемое имя</th>
                <th>Роль</th>
                <th>Протокол</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const isSelf = me?.id === u.id;
                const pendingRole = roles[u.id] ?? u.role;
                const changed = pendingRole !== u.role;
                return (
                  <tr key={u.id}>
                    <td>{u.username}</td>
                    <td>{u.display_name}</td>
                    <td>
                      <select
                        value={pendingRole}
                        disabled={isSelf || savingId === u.id}
                        onChange={(e) =>
                          setRoles((prev) => ({ ...prev, [u.id]: e.target.value }))
                        }
                        aria-label={`Роль для ${u.username}`}
                      >
                        {ASSIGNABLE_ROLES.map((r) => (
                          <option key={r.id} value={r.id}>
                            {r.label}
                          </option>
                        ))}
                      </select>
                      {isSelf && (
                        <span className="dash-card-note" style={{ display: "block", marginTop: 4 }}>
                          это вы
                        </span>
                      )}
                    </td>
                    <td>
                      {u.profile_complete ? (
                        <a
                          className="btn btn-outline btn-sm"
                          href={api.adminUserProtocolDraftPdfUrl(u.id)}
                          style={{ textDecoration: "none", whiteSpace: "nowrap" }}
                        >
                          Черновик PDF
                        </a>
                      ) : (
                        <span className="dash-card-note" title="Заполните профиль пользователя">
                          профиль неполный
                        </span>
                      )}
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        disabled={isSelf || !changed || savingId === u.id}
                        onClick={() => void onSaveRole(u)}
                      >
                        {savingId === u.id ? "Сохранение…" : "Сохранить"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </DashboardLayout>
  );
}
