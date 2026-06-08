import { Link, useLocation, useNavigate } from "react-router-dom";
import { safetyGroupLabel } from "../constants/safetyGroups";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useMobileNav } from "../hooks/useMobileNav";
import { useSidebarOnScroll } from "../hooks/useSidebarOnScroll";

const NAV_BASE = [
  { to: "/cabinet", label: "Главная", key: "home" },
  { to: "/training", label: "Тренировка", key: "training" },
  { to: "/exam", label: "Экзамен", key: "exam" },
  { to: "/manuals", label: "Нормативные документы", key: "manuals" },
] as const;

const NAV_ADMIN = { to: "/admin/users", label: "Пользователи", key: "admin" } as const;
const NAV_SAFETY_GROUPS = {
  to: "/staff/safety-groups",
  label: "Группы ЭБ",
  key: "safety-groups",
} as const;
const NAV_CONSTRUCTOR = {
  to: "/constructor",
  label: "Конструктор билетов",
  key: "constructor",
} as const;

const LOGO_MASCOT = "/razvivaisia/assets/images/logo-mascot.gif";
const LOGO_BRAND = "/razvivaisia/assets/images/y-razvivaisia-logo.png";
const AVATAR = "/razvivaisia/assets/images/hedgehog-avatar.svg";
const HELPY_LOGO = "/razvivaisia/assets/images/helpy.png";
const HELPY_SUPPORT_URL =
  "https://messenger.360.yandex.ru/#/user/f7469409-2aec-96de-46c5-5a4cd52f4227";

export default function DashboardLayout({
  children,
  active,
}: {
  children: React.ReactNode;
  active: "home" | "manuals" | "training" | "exam" | "admin" | "constructor" | "safety-groups";
}) {
  const { user, setUser } = useAuth();
  const editorNav = user?.can_create_tests ? [NAV_CONSTRUCTOR] : [];
  const staffNav =
    user?.role === "admin" || user?.role === "ezh" ? [NAV_SAFETY_GROUPS] : [];
  const adminNav = user?.role === "admin" ? [NAV_ADMIN, ...editorNav, ...staffNav] : [...editorNav, ...staffNav];
  const navItems = [...NAV_BASE, ...adminNav];
  const navigate = useNavigate();
  const location = useLocation();
  const { open, toggle, close } = useMobileNav();
  const { mainRef, collapsed, showDesktopSidebar, toggleDesktopSidebar } = useSidebarOnScroll(
    location.pathname,
    close,
    open
  );

  const onBurgerClick = () => {
    if (window.innerWidth <= 768) {
      toggle();
      return;
    }
    if (collapsed) {
      toggleDesktopSidebar();
    }
  };

  const pageWrapperClass = [
    "page-wrapper",
    "page-wrapper--dashboard",
    collapsed ? "page-wrapper--sidebar-collapsed" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const mainLayoutClass = [
    "main-layout",
    !showDesktopSidebar ? "main-layout--sidebar-collapsed" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const sidebarClass = ["sidebar", open ? "active" : "", !showDesktopSidebar ? "sidebar--hidden" : ""]
    .filter(Boolean)
    .join(" ");

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
    <div className={pageWrapperClass}>
      <header className="header">
        <div className="header-logo">
          <button
            type="button"
            className={`burger-menu ${open ? "active" : ""}`}
            id="burgerMenu"
            aria-label={collapsed ? "Развернуть меню" : "Открыть меню"}
            aria-expanded={open || (collapsed && showDesktopSidebar)}
            onClick={onBurgerClick}
          >
            <span />
            <span />
            <span />
          </button>
          <Link to="/cabinet" className="header-logo-brand">
            <img src={LOGO_MASCOT} alt="" className="header-logo-mascot" />
            <img src={LOGO_BRAND} alt="Y Развивайся" className="header-logo-y-razvivaisia" />
          </Link>
        </div>
        <div className="header-user header-user-actions">
          <img src={AVATAR} alt="" className="header-user-avatar" />
          <div className="header-user-info">
            <div className="header-user-name">{user?.display_name}</div>
            <div className="header-user-group">
              {user?.role === "kot" ? safetyGroupLabel(user.safety_group) : user?.role_label}
            </div>
          </div>
          <button type="button" className="dash-link-btn" onClick={() => void logout()}>
            Выход
          </button>
        </div>
      </header>

      <div className={mainLayoutClass}>
        <div
          className={`sidebar-overlay ${open ? "active" : ""}`}
          id="sidebarOverlay"
          onClick={close}
          onKeyDown={() => undefined}
          role="presentation"
        />
        <aside className={sidebarClass} id="sidebar">
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
            <p className="sidebar-support-caption">Если что то сломалось</p>
            <a
              href={HELPY_SUPPORT_URL}
              className="sidebar-helpy-btn"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Открыть поддержку Helpy в Яндекс Мессенджере"
            >
              <img src={HELPY_LOGO} alt="Helpy — служба поддержки" className="sidebar-helpy-img" />
            </a>
          </div>
        </aside>

        <main className="main-content" ref={mainRef}>
          <div className="content-wrapper">{children}</div>
        </main>
      </div>
    </div>
  );
}
