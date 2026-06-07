import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { axiosErrorMessage } from "../api/getReact";
import { SAFETY_GROUPS } from "../constants/safetyGroups";
import DashboardLayout from "../layout/DashboardLayout";
import type { KotUser } from "../types/api";

export default function KotSafetyGroupsPage() {
  const [users, setUsers] = useState<KotUser[]>([]);
  const [groups, setGroups] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [savingId, setSavingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const list = await api.listKotUsers();
      setUsers(list);
      setGroups(Object.fromEntries(list.map((u) => [u.id, u.safety_group])));
    } catch (err) {
      setError(axiosErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const onSave = async (target: KotUser) => {
    const group = groups[target.id];
    if (!group || group === target.safety_group) return;
    setSavingId(target.id);
    setMessage("");
    setError("");
    try {
      const updated = await api.updateKotSafetyGroup(target.id, group);
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      setGroups((prev) => ({ ...prev, [updated.id]: updated.safety_group }));
      setMessage(`Группа пользователя ${updated.username} обновлена`);
    } catch (err) {
      setError(axiosErrorMessage(err));
    } finally {
      setSavingId(null);
    }
  };

  return (
    <DashboardLayout active="safety-groups">
      <div className="dash-page-intro">
        <h1 className="dash-section-title">Группы по электробезопасности</h1>
        <p className="dash-card-note">
          Назначение группы I, II, III или IV пользователям с ролью Кот. От группы зависит, какой
          экзамен и тренировочные тесты будут доступны.
        </p>
      </div>
      {error && <p className="auth-error">{error}</p>}
      {message && <p className="dash-card-note">{message}</p>}
      {loading ? (
        <p className="dash-card-note">Загрузка…</p>
      ) : users.length === 0 ? (
        <p className="dash-card-note">Пользователей с ролью Кот пока нет.</p>
      ) : (
        <div className="dash-table-wrap">
          <table className="dash-table">
            <thead>
              <tr>
                <th>Логин</th>
                <th>Имя</th>
                <th>Группа по ЭБ</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const pending = groups[u.id] ?? u.safety_group;
                const changed = pending !== u.safety_group;
                return (
                  <tr key={u.id}>
                    <td>{u.username}</td>
                    <td>{u.display_name}</td>
                    <td>
                      <select
                        value={pending}
                        disabled={savingId === u.id}
                        onChange={(e) =>
                          setGroups((prev) => ({ ...prev, [u.id]: e.target.value }))
                        }
                        aria-label={`Группа для ${u.username}`}
                      >
                        {SAFETY_GROUPS.map((g) => (
                          <option key={g.id} value={g.id}>
                            {g.label}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        disabled={!changed || savingId === u.id}
                        onClick={() => void onSave(u)}
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
