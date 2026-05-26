import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function HomePage() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/cabinet" replace />;

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <span className="dash-logo">
            <span className="dash-logo-mark">Я</span>
            <span className="dash-logo-text">
              Разви<span className="dash-logo-accent">вайся</span>
            </span>
          </span>
        </div>
        <p className="dash-card-note" style={{ textAlign: "center" }}>
          Платформа для обучения и сдачи экзамена по электробезопасности
        </p>
        <Link to="/register" className="dash-exam-btn" style={{ display: "block", textAlign: "center" }}>
          Создать аккаунт
        </Link>
        <p className="auth-links">
          <Link to="/login">Войти</Link>
        </p>
      </div>
    </div>
  );
}
