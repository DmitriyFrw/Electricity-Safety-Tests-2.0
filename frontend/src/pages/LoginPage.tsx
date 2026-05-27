import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const fd = new FormData(e.target as HTMLFormElement);
    try {
      const user = await api.login(
        String(fd.get("username")),
        String(fd.get("password"))
      );
      setUser(user);
      navigate("/cabinet");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Вход</h1>
        {error && <p className="auth-error">{error}</p>}
        <form onSubmit={onSubmit}>
          <label htmlFor="username">Логин</label>
          <input id="username" name="username" required autoComplete="username" />
          <label htmlFor="password">Пароль</label>
          <input id="password" name="password" type="password" required autoComplete="current-password" />
          <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
            {loading ? "Вход…" : "Войти"}
          </button>
        </form>
        <p className="auth-links">
          <Link to="/register">Регистрация</Link>
        </p>
      </div>
    </div>
  );
}
