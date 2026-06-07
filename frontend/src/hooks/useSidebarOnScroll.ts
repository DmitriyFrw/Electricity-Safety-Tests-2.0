import { useCallback, useEffect, useRef, useState } from "react";

const SCROLL_THRESHOLD_PX = 12;

export function useSidebarOnScroll(
  pathname: string,
  closeMobileSidebar: () => void,
  mobileOpen: boolean
) {
  const mainRef = useRef<HTMLElement | null>(null);
  const lastScrollTop = useRef(0);
  const [collapsed, setCollapsed] = useState(false);
  const [desktopExpanded, setDesktopExpanded] = useState(false);

  const resetAtTop = useCallback(() => {
    setCollapsed(false);
    setDesktopExpanded(false);
  }, []);

  const collapse = useCallback(() => {
    setCollapsed(true);
    setDesktopExpanded(false);
  }, []);

  const toggleDesktopSidebar = useCallback(() => {
    setDesktopExpanded((open) => !open);
  }, []);

  useEffect(() => {
    lastScrollTop.current = 0;
    resetAtTop();
    const el = mainRef.current;
    if (el) el.scrollTop = 0;
    window.scrollTo(0, 0);
  }, [pathname, resetAtTop]);

  useEffect(() => {
    const el = mainRef.current;

    const readScrollTop = (): number => {
      if (el && el.scrollHeight > el.clientHeight + 1) {
        return el.scrollTop;
      }
      return window.scrollY || document.documentElement.scrollTop;
    };

    const onScroll = () => {
      const scrollTop = readScrollTop();

      if (scrollTop <= 0) {
        resetAtTop();
      } else if (scrollTop > lastScrollTop.current && scrollTop > SCROLL_THRESHOLD_PX) {
        collapse();
        if (mobileOpen && window.innerWidth <= 768) {
          closeMobileSidebar();
        }
      }

      lastScrollTop.current = scrollTop;
    };

    el?.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      el?.removeEventListener("scroll", onScroll);
      window.removeEventListener("scroll", onScroll);
    };
  }, [collapse, resetAtTop, closeMobileSidebar, mobileOpen]);

  const showDesktopSidebar = !collapsed || desktopExpanded;

  return {
    mainRef,
    collapsed,
    showDesktopSidebar,
    toggleDesktopSidebar,
    collapse,
  };
}
