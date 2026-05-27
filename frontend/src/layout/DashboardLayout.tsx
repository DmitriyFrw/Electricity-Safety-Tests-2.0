import { Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

const NAV = [
  { to: "/cabinet", label: "Главная", key: "home" },
  { to: "/manuals", label: "Мануалы", key: "manuals" },
  { to: "/training", label: "Обучение", key: "training" },
  { to: "/exam", label: "Экзамен", key: "exam" },
] as const;

export default function DashboardLayout({
  children,
  active,
}: {
  children: React.ReactNode;
  active: "home" | "manuals" | "training" | "exam";
}) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const logout = async () => {
    await api.logout();
    navigate("/login");
    window.location.reload();
  };

  return (
    <div className="dash-shell">
      <aside className="dash-sidebar">
        <Link to="/cabinet" className="dash-logo">
          <span className="dash-logo-mark">Я</span>
          <span className="dash-logo-text">
            Разви<span className="dash-logo-accent">вайся</span>
          </span>
        </Link>
        <p className="dash-logo-sub">
          ПЛАТФОРМА ДЛЯ ОБУЧЕНИЯ И СДАЧИ ЭКЗАМЕНА ПО ЭЛЕКТРОБЕЗОПАСНОСТИ
        </p>
        <nav className="dash-nav">
          {NAV.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={`dash-nav-item ${active === item.key || location.pathname.startsWith(item.to) ? "is-active" : ""}`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="dash-support">
          <p className="dash-support-title">Поддержка</p>
          <p>8-800-555-35-35</p>
          <p>support-@ivan.ru</p>
          <p className="dash-support-hours">Пн — Пт, 9:00 — 00:00</p>
        </div>
      </aside>
      <div className="dash-main">
        <header className="dash-topbar">
          <div className="dash-user">
            <span className="dash-avatar" aria-hidden="true">
              <svg viewBox="0 0 48 48" width="40" height="40">
                <circle cx="24" cy="18" r="10" fill="#c4cdd8" />
                <path
                  d="M8 42c2-10 10-14 16-14s14 4 16 14"
                  fill="#9aa8bc"
                />
              </svg>
            </span>
            <div>
              <div className="dash-user-name">{user?.display_name}</div>
              <div className="dash-user-meta">
                {user?.role_label} · {user?.safety_group} группа {user?.safety_group_desc}
              </div>
            </div>
          </div>
          <button type="button" className="dash-link-btn" onClick={() => void logout()}>
            Выход
          </button>
        </header>
        <div className="dash-content">{children}</div>
      </div>
    </div>
  );
}
