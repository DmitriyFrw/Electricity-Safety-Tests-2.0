import { useCallback, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

const DESKTOP_MIN = 1025;

function isDesktopViewport() {
  return typeof window !== "undefined" && window.innerWidth >= DESKTOP_MIN;
}

export function useStaffSidebar() {
  const [expanded, setExpanded] = useState(true);
  const location = useLocation();

  const collapse = useCallback(() => setExpanded(false), []);
  const toggle = useCallback(() => setExpanded((v) => !v), []);

  useEffect(() => {
    setExpanded(isDesktopViewport());
  }, []);

  useEffect(() => {
    if (!isDesktopViewport()) collapse();
  }, [location.pathname, collapse]);

  useEffect(() => {
    const lockScroll = expanded && !isDesktopViewport();
    document.body.style.overflow = lockScroll ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [expanded]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") collapse();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [collapse]);

  return { expanded, toggle, collapse };
}
