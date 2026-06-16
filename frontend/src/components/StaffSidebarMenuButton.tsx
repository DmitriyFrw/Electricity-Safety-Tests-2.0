export default function StaffSidebarMenuButton({
  expanded,
  onClick,
}: {
  expanded: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className="staff-sidebar-menu-btn"
      aria-label={expanded ? "Свернуть меню" : "Развернуть меню"}
      aria-expanded={expanded}
      onClick={onClick}
    >
      {expanded ? (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
          <path d="M15 6l-6 6 6 6" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      )}
    </button>
  );
}
