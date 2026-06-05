import { useEffect, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

export const SIDEBAR_CONSTRUCTOR_SLOT_ID = "sidebar-constructor-slot";

export default function SidebarPortal({ children }: { children: ReactNode }) {
  const [target, setTarget] = useState<HTMLElement | null>(null);

  useEffect(() => {
    setTarget(document.getElementById(SIDEBAR_CONSTRUCTOR_SLOT_ID));
  }, []);

  if (!target) return null;
  return createPortal(children, target);
}
