import { Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import BrandLogo from "./BrandLogo";
import { useAuth } from "../auth/AuthContext";
import { staffNavForUser } from "../navigation/staffNav";
import { userInitials } from "../utils/userInitials";

export default function StaffSidebar({
  expanded = true,
  onClose,
}: {
  expanded?: boolean;
  onClose?: () => void;
}) {
  const { user, setUser } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const items = staffNavForUser(user);

  if (!user || items.length === 0) return null;

  const onNav = () => {
    onClose?.();
  };

  const onLogout = async () => {
    try {
      await api.logout();
    } catch {
      /* ignore */
    }
    setUser(null);
    onClose?.();
    navigate("/login");
  };

  const sidebarClass = [
    "constructor-sidebar",
    expanded ? "constructor-sidebar--expanded" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <>
      <button
        type="button"
        className={`constructor-sidebar-backdrop${expanded ? " constructor-sidebar-backdrop--open" : ""}`}
        aria-label="Закрыть меню"
        onClick={onClose}
        tabIndex={expanded ? 0 : -1}
      />
      <aside className={sidebarClass} aria-label="Навигация" aria-hidden={!expanded}>
        <div className="constructor-sidebar__brand">
          <BrandLogo variant="sidebar" />
        </div>
        <nav className="constructor-sidebar__nav">
          {items.map((item) => {
            const active = item.match(location.pathname);
            return (
              <Link
                key={item.key}
                to={item.to}
                className={`constructor-sidebar__link${active ? " constructor-sidebar__link--active" : ""}`}
                onClick={onNav}
                tabIndex={expanded ? 0 : -1}
              >
                <span className="constructor-sidebar__icon">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="constructor-sidebar__profile">
          <div className="constructor-sidebar__profile-row">
            <span className="constructor-sidebar__avatar">{userInitials(user)}</span>
            <div className="constructor-sidebar__profile-text">
              <strong>{user.role_label || user.display_name}</strong>
              <span>{user.username}</span>
            </div>
          </div>
          <button
            type="button"
            className="constructor-sidebar__logout"
            onClick={() => void onLogout()}
            tabIndex={expanded ? 0 : -1}
          >
            Выйти
          </button>
        </div>
      </aside>
    </>
  );
}
