import axios, { type AxiosError } from "axios";

/** Общий клиент: cookie-сессия, JSON с backend. */
export const apiClient = axios.create({
  baseURL: "/api",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

type ValidationIssue = { loc?: (string | number)[]; msg?: string };

function formatApiDetail(detail: unknown): string | null {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (!Array.isArray(detail)) return null;
  const lines = detail
    .map((item: ValidationIssue) => {
      if (!item || typeof item !== "object" || typeof item.msg !== "string") return null;
      const loc = (item.loc ?? []).filter((x) => x !== "body" && x !== "query");
      const where = loc.length ? `${loc.map(String).join(".")}: ` : "";
      return `${where}${item.msg}`;
    })
    .filter((line): line is string => Boolean(line));
  return lines.length ? lines.join("; ") : null;
}

export function axiosErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const ax = err as AxiosError<{ detail?: unknown }>;
    const formatted = formatApiDetail(ax.response?.data?.detail);
    if (formatted) return formatted;
    if (ax.response?.status === 422) return "Проверьте введённые данные (ошибка валидации)";
    return ax.message;
  }
  if (err instanceof Error) return err.message;
  return "Ошибка запроса";
}

function isCsrf403(detail: unknown): boolean {
  if (typeof detail !== "string") return false;
  // Точное значение зависит от backend, но в тексте всегда встречается "CSRF" или "токен".
  return detail.includes("CSRF") || detail.toLowerCase().includes("csrf") || detail.includes("токен");
}

// Централизованная обработка ошибок авторизации/сервера.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!axios.isAxiosError(error)) return Promise.reject(error);
    const ax = error as AxiosError<{ detail?: string }>;

    const status = ax.response?.status;
    const detail = ax.response?.data?.detail;
    const corrId = ax.response?.headers?.["x-correlation-id"];

    if (status === 401 || status === 403) {
      // CSRF 403 должен обрабатываться CSRFMiddleware на клиенте (retry в csrf.ts),
      // поэтому не дергаем auth-редирект для него.
      if (status === 403 && isCsrf403(detail)) return Promise.reject(error);

      window.dispatchEvent(
        new CustomEvent("auth-error", {
          detail: { status, detail, correlationId: corrId },
        })
      );
    } else if (status && status >= 500) {
      window.dispatchEvent(
        new CustomEvent("server-error", {
          detail: { status, detail, correlationId: corrId },
        })
      );
    }

    return Promise.reject(error);
  }
);
