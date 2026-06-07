import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { axiosErrorMessage } from "../api/getReact";
import { useAuth } from "../auth/AuthContext";

const LOGO_MASCOT = "/razvivaisia/assets/images/logo-mascot.gif";

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
      setError(axiosErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page auth-page--login">
      <div className="auth-card">
        <div className="auth-brand">
          <img src={LOGO_MASCOT} alt="" className="auth-brand-mascot" />
          <h1 className="auth-brand-title">
            Развивайс<span className="auth-brand-accent">я</span>
          </h1>
          <p className="auth-brand-subtitle">образовательная платформа</p>
        </div>
        {error && <p className="auth-error">{error}</p>}
        <form className="auth-form" onSubmit={onSubmit}>
          <label htmlFor="username">Логин</label>
          <input id="username" name="username" required autoComplete="username" />
          <label htmlFor="password">Пароль</label>
          <input id="password" name="password" type="password" required autoComplete="current-password" />
          <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
            {loading ? "Вход…" : "Договорились!"}
          </button>
        </form>
        <p className="auth-links">
          <Link to="/register">Регистрация</Link>
        </p>
      </div>
    </div>
  );
}
