import { Link, useNavigate } from "react-router-dom";
import BrandLogo from "../components/BrandLogo";
import StaffSidebar from "../components/StaffSidebar";
import StaffSidebarMenuButton from "../components/StaffSidebarMenuButton";
import { SIDEBAR_CONSTRUCTOR_SLOT_ID } from "../components/SidebarPortal";
import { useAuth } from "../auth/AuthContext";
import { useStaffSidebar } from "../hooks/useStaffSidebar";
import { isStaffUser } from "../navigation/staffNav";
import { userInitials } from "../utils/userInitials";

const NAV = [
  { to: "/", label: "Главная", key: "home" },
  { to: "/training", label: "Тренировочные тесты", key: "training" },
  { to: "/exam", label: "Экзамен", key: "exam" },
  { to: "/results", label: "Результаты", key: "results" },
] as const;

export type TopNavActive = (typeof NAV)[number]["key"];

export default function TopNavLayout({
  children,
  active,
  constructorRail,
}: {
  children: React.ReactNode;
  active?: TopNavActive;
  /** Боковая навигация по билетам в конструкторе (SidebarPortal). */
  constructorRail?: boolean;
}) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const showStaffSidebar = isStaffUser(user);
  const staffSidebar = useStaffSidebar();

  const onNavClick = (to: string, e: React.MouseEvent) => {
    if (!user && to !== "/") {
      e.preventDefault();
      navigate("/login");
    }
  };

  const shellClass = showStaffSidebar ? "constructor-app top-nav-app" : "mockup-app";

  return (
    <div
      className={`${shellClass}${showStaffSidebar ? (staffSidebar.expanded ? " constructor-app--sidebar-expanded" : " constructor-app--sidebar-collapsed") : ""}`}
    >
      {showStaffSidebar && (
        <StaffSidebar expanded={staffSidebar.expanded} onClose={staffSidebar.collapse} />
      )}

      <div className={showStaffSidebar ? "constructor-main" : undefined}>
        <header className="top-nav">
          <div className="top-nav__inner">
            {showStaffSidebar && (
              <StaffSidebarMenuButton expanded={staffSidebar.expanded} onClick={staffSidebar.toggle} />
            )}
            <BrandLogo />
            <nav className="top-nav__links" aria-label="Основная навигация">
              {NAV.map((item) => (
                <Link
                  key={item.key}
                  to={item.to}
                  className={`top-nav__link${active === item.key ? " top-nav__link--active" : ""}`}
                  onClick={(e) => onNavClick(item.to, e)}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
            <div className="top-nav__actions">
              <button type="button" className="top-nav__bell" aria-label="Уведомления">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
                  <path d="M13.73 21a2 2 0 01-3.46 0" />
                </svg>
              </button>
              {user ? (
                <Link to="/cabinet" className="top-nav__avatar" title="Личный кабинет">
                  {userInitials(user)}
                </Link>
              ) : (
                <Link to="/login" className="top-nav__login">
                  Войти
                </Link>
              )}
            </div>
          </div>
        </header>
        <main className={`mockup-main${constructorRail ? " mockup-main--constructor" : ""}`}>
          {constructorRail ? (
            <div className="constructor-layout">
              <div id={SIDEBAR_CONSTRUCTOR_SLOT_ID} className="constructor-rail sidebar-constructor-slot" />
              <div className="constructor-content">{children}</div>
            </div>
          ) : (
            children
          )}
        </main>
      </div>
    </div>
  );
}
