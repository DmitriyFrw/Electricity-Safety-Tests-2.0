import type { ReactNode } from "react";
import StaffSidebar from "../components/StaffSidebar";
import StaffSidebarMenuButton from "../components/StaffSidebarMenuButton";
import { useStaffSidebar } from "../hooks/useStaffSidebar";

export default function AdminLayout({ children }: { children: ReactNode }) {
  const staffSidebar = useStaffSidebar();

  return (
    <div
      className={`constructor-app${staffSidebar.expanded ? " constructor-app--sidebar-expanded" : " constructor-app--sidebar-collapsed"}`}
    >
      <StaffSidebar expanded={staffSidebar.expanded} onClose={staffSidebar.collapse} />
      <div className="constructor-main">
        <header className="constructor-topbar constructor-topbar--admin">
          <div className="constructor-topbar__title-row">
            <StaffSidebarMenuButton expanded={staffSidebar.expanded} onClick={staffSidebar.toggle} />
          </div>
        </header>
        <main className="admin-content">{children}</main>
      </div>
    </div>
  );
}
