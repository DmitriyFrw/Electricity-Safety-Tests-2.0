import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export default function RegisterPage() {
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
      const user = await api.register(
        String(fd.get("username")),
        String(fd.get("password")),
        String(fd.get("password2"))
      );
      setUser(user);
      navigate("/cabinet");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка регистрации");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Регистрация</h1>
        {error && <p className="auth-error">{error}</p>}
        <form onSubmit={onSubmit}>
          <label htmlFor="username">Логин</label>
          <input id="username" name="username" required />
          <label htmlFor="password">Пароль</label>
          <input id="password" name="password" type="password" required />
          <label htmlFor="password2">Пароль ещё раз</label>
          <input id="password2" name="password2" type="password" required />
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "…" : "Зарегистрироваться"}
          </button>
        </form>
        <p className="auth-links">
          <Link to="/login">Уже есть аккаунт</Link>
        </p>
      </div>
    </div>
  );
}
