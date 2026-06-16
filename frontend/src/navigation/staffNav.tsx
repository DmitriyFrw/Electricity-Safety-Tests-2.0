import type { User } from "../types/api";

export type StaffRole = "admin" | "ezh";

export type StaffNavKey =
  | "dashboard"
  | "users"
  | "tickets"
  | "results"
  | "safetyGroups"
  | "reports"
  | "profile";

export type StaffNavItem = {
  key: StaffNavKey;
  to: string;
  label: string;
  roles: StaffRole[];
  match: (pathname: string) => boolean;
  icon: React.ReactNode;
};

const IconDashboard = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
    <path d="M4 19V5a1 1 0 011-1h4v15H4zM10 19V9h4v10h-4zM16 19V3h4a1 1 0 011 1v15h-5z" />
  </svg>
);

const IconUsers = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
    <path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M22 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
  </svg>
);

const IconTickets = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
    <rect x="3" y="5" width="18" height="14" rx="2" />
    <path d="M7 9h10M7 13h6" />
  </svg>
);

const IconResults = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
    <path d="M18 20V10M12 20V4M6 20v-6" />
  </svg>
);

const IconReports = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
    <path d="M3 3h18v18H3zM7 7h4v10H7zM13 11h4v6h-4z" />
  </svg>
);

const IconProfile = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 20v-1a4 4 0 014-4h8a4 4 0 014 4v1" />
  </svg>
);

export const STAFF_NAV: StaffNavItem[] = [
  {
    key: "dashboard",
    to: "/admin",
    label: "Панель управления",
    roles: ["admin"],
    match: (p) => p === "/admin",
    icon: <IconDashboard />,
  },
  {
    key: "users",
    to: "/admin/users",
    label: "Пользователи",
    roles: ["admin"],
    match: (p) => p.startsWith("/admin/users"),
    icon: <IconUsers />,
  },
  {
    key: "tickets",
    to: "/constructor",
    label: "Билеты",
    roles: ["admin", "ezh"],
    match: (p) => p === "/constructor" || p.startsWith("/constructor/") || p.startsWith("/tests/"),
    icon: <IconTickets />,
  },
  {
    key: "results",
    to: "/results",
    label: "Результаты",
    roles: ["admin", "ezh"],
    match: (p) => p === "/results" || p.includes("/result/"),
    icon: <IconResults />,
  },
  {
    key: "safetyGroups",
    to: "/staff/safety-groups",
    label: "Группы ЭБ",
    roles: ["admin", "ezh"],
    match: (p) => p.startsWith("/staff/safety-groups"),
    icon: <IconUsers />,
  },
  {
    key: "reports",
    to: "/staff/exam-schedule",
    label: "Отчёты",
    roles: ["admin", "ezh"],
    match: (p) => p.startsWith("/staff/exam-schedule"),
    icon: <IconReports />,
  },
  {
    key: "profile",
    to: "/cabinet",
    label: "Мой профиль",
    roles: ["admin", "ezh"],
    match: (p) => p === "/cabinet",
    icon: <IconProfile />,
  },
];

export function isStaffUser(user: User | null): user is User {
  return user?.role === "admin" || user?.role === "ezh";
}

export function staffNavForUser(user: User | null): StaffNavItem[] {
  if (!isStaffUser(user)) return [];
  const role = user.role as StaffRole;
  return STAFF_NAV.filter((item) => item.roles.includes(role));
}
