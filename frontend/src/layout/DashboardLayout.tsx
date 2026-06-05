import { Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useMobileNav } from "../hooks/useMobileNav";

const NAV_BASE = [
  { to: "/cabinet", label: "Главная", key: "home" },
  { to: "/training", label: "Тренировка", key: "training" },
  { to: "/exam", label: "Экзамен", key: "exam" },
  { to: "/manuals", label: "Нормативные документы", key: "manuals" },
] as const;

const NAV_ADMIN = { to: "/admin/users", label: "Пользователи", key: "admin" } as const;
const NAV_CONSTRUCTOR = {
  to: "/constructor",
  label: "Конструктор билетов",
  key: "constructor",
} as const;

const LOGO_MASCOT = "/razvivaisia/assets/images/logo-mascot.gif";
const AVATAR = "/razvivaisia/assets/images/hedgehog-avatar.svg";

export default function DashboardLayout({
  children,
  active,
}: {
  children: React.ReactNode;
  active: "home" | "manuals" | "training" | "exam" | "admin" | "constructor";
}) {
  const { user, setUser } = useAuth();
  const editorNav = user?.can_create_tests ? [NAV_CONSTRUCTOR] : [];
  const adminNav = user?.role === "admin" ? [NAV_ADMIN, ...editorNav] : editorNav;
  const navItems = [...NAV_BASE, ...adminNav];
  const navigate = useNavigate();
  const location = useLocation();
  const { open, toggle, close } = useMobileNav();

  const logout = async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
      navigate("/login");
    }
  };

  const isActive = (to: string, key: string) =>
    active === key || location.pathname === to || location.pathname.startsWith(`${to}/`);

  return (
    <div className="page-wrapper">
      <header className="header">
        <div className="header-logo">
          <button
            type="button"
            className={`burger-menu ${open ? "active" : ""}`}
            id="burgerMenu"
            aria-label="Открыть меню"
            onClick={toggle}
          >
            <span />
            <span />
            <span />
          </button>
          <Link to="/cabinet" className="header-logo-brand">
            <img src={LOGO_MASCOT} alt="" className="header-logo-mascot" />
            <span className="header-logo-mark">209AO</span>
          </Link>
        </div>
        <div className="header-user header-user-actions">
          <img src={AVATAR} alt="" className="header-user-avatar" />
          <div className="header-user-info">
            <div className="header-user-name">{user?.display_name}</div>
            <div className="header-user-group">
              <span>{user?.safety_group} группа</span> {user?.safety_group_desc}
            </div>
          </div>
          <button type="button" className="dash-link-btn" onClick={() => void logout()}>
            Выход
          </button>
        </div>
      </header>

      <div className="main-layout">
        <div
          className={`sidebar-overlay ${open ? "active" : ""}`}
          id="sidebarOverlay"
          onClick={close}
          onKeyDown={() => undefined}
          role="presentation"
        />
        <aside className={`sidebar ${open ? "active" : ""}`} id="sidebar">
          <nav className="sidebar-nav">
            <ul className="sidebar-menu">
              {navItems.map((item) => (
                <li key={item.to}>
                  <Link
                    to={item.to}
                    className={`sidebar-menu-item ${isActive(item.to, item.key) ? "active" : ""}`}
                    onClick={close}
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
          <div
            id="sidebar-constructor-slot"
            className="sidebar-constructor-slot"
            aria-live="polite"
          />
          <div className="sidebar-support">
            <div className="sidebar-support-title">Служба поддержки</div>
            <a href="tel:88005553535" className="sidebar-support-phone">
              8-800-555-35-35
            </a>
            <a href="mailto:support@ivan.ru" className="sidebar-support-email">
              support@ivan.ru
            </a>
            <div className="sidebar-support-hours">Пн - Пт с 9:00 - 00:00</div>
          </div>
        </aside>

        <main className="main-content">
          <div className="content-wrapper">{children}</div>
        </main>
      </div>
    </div>
  );
}
