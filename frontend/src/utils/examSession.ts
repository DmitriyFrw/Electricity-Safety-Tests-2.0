const GUARD_PREFIX = "exam_take_active_";
const CSRF_STORAGE_KEY = "csrf_token";

export function examGuardKey(testId: number): string {
  return `${GUARD_PREFIX}${testId}`;
}

export function isExamPageRefresh(testId: number): boolean {
  return sessionStorage.getItem(examGuardKey(testId)) === "1";
}

export function markExamPageActive(testId: number): void {
  sessionStorage.setItem(examGuardKey(testId), "1");
}

export function clearExamPageGuard(testId: number): void {
  sessionStorage.removeItem(examGuardKey(testId));
}

/** POST abandon с keepalive — для закрытия вкладки / ухода со страницы. */
export function abandonExamKeepalive(testId: number): void {
  const csrf =
    sessionStorage.getItem(CSRF_STORAGE_KEY) ??
    (typeof document !== "undefined"
      ? document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.content
      : null);
  void fetch(`/api/tests/${testId}/exam/abandon`, {
    method: "POST",
    credentials: "include",
    keepalive: true,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(csrf ? { "X-CSRF-Token": csrf } : {}),
    },
  });
}
