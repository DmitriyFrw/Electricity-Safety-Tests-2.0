import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import StaffSidebar from "../components/StaffSidebar";
import StaffSidebarMenuButton from "../components/StaffSidebarMenuButton";
import { SIDEBAR_CONSTRUCTOR_SLOT_ID } from "../components/SidebarPortal";
import { useAuth } from "../auth/AuthContext";
import { useStaffSidebar } from "../hooks/useStaffSidebar";
import { isStaffUser } from "../navigation/staffNav";
import { userInitials } from "../utils/userInitials";

export default function ConstructorLayout({
  children,
  title = "Конструктор билетов",
  createLabel = "Создать тест",
  showCreate = true,
  editing = false,
  onCreateClick,
}: {
  children: ReactNode;
  title?: string;
  createLabel?: string;
  showCreate?: boolean;
  editing?: boolean;
  onCreateClick?: () => void;
}) {
  const { user } = useAuth();
  const staffSidebar = useStaffSidebar();
  const showStaffSidebar = isStaffUser(user);

  return (
    <div
      className={`constructor-app${staffSidebar.expanded && showStaffSidebar ? " constructor-app--sidebar-expanded" : " constructor-app--sidebar-collapsed"}`}
    >
      {showStaffSidebar && (
        <StaffSidebar expanded={staffSidebar.expanded} onClose={staffSidebar.collapse} />
      )}

      <div className="constructor-main">
        <header className="constructor-topbar">
          <div className="constructor-topbar__title-row">
            {showStaffSidebar && (
              <StaffSidebarMenuButton expanded={staffSidebar.expanded} onClick={staffSidebar.toggle} />
            )}
            <h1 className="constructor-topbar__title">{title}</h1>
          </div>
          <div className="constructor-topbar__actions">
            <button type="button" className="constructor-topbar__icon-btn" aria-label="Уведомления">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
                <path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.73 21a2 2 0 01-3.46 0" />
              </svg>
            </button>
            <Link to="/cabinet" className="constructor-topbar__avatar" title="Личный кабинет">
              {user ? userInitials(user) : "?"}
            </Link>
            {showCreate && onCreateClick && (
              <button
                type="button"
                className="mockup-btn mockup-btn--primary constructor-topbar__create"
                onClick={onCreateClick}
              >
                {createLabel}
              </button>
            )}
          </div>
        </header>

        <div className={`constructor-body${editing ? " constructor-body--editor" : ""}`}>
          {editing ? (
            <div className="constructor-layout">
              <div id={SIDEBAR_CONSTRUCTOR_SLOT_ID} className="constructor-rail sidebar-constructor-slot" />
              <div className="constructor-content">{children}</div>
            </div>
          ) : (
            children
          )}
        </div>
      </div>
    </div>
  );
}
