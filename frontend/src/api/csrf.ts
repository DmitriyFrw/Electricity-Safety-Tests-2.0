import type { InternalAxiosRequestConfig } from "axios";
import { getReact } from "./getReact";
import { apiClient } from "./axios";

type CsrfAxiosConfig = InternalAxiosRequestConfig & { _csrfRetry?: boolean };

let csrfToken: string | null = null;

const UNSAFE = new Set(["post", "put", "patch", "delete"]);

/** Загрузить CSRF-токен с backend (GET /api/auth/csrf) перед мутациями. */
export async function initCsrf(): Promise<string> {
  const { csrf_token } = await getReact<{ csrf_token: string }>("/auth/csrf");
  csrfToken = csrf_token;
  sessionStorage.setItem("csrf_token", csrf_token);
  return csrf_token;
}

export function getCsrfToken(): string | null {
  return csrfToken;
}

export function setCsrfToken(token: string): void {
  csrfToken = token;
  sessionStorage.setItem("csrf_token", token);
}

/** Подключить заголовок X-CSRF-Token ко всем небезопасным запросам axios. */
export function setupCsrfInterceptor(): void {
  apiClient.interceptors.request.use((config) => {
    const method = (config.method ?? "get").toLowerCase();
    if (UNSAFE.has(method) && csrfToken) {
      config.headers.set("X-CSRF-Token", csrfToken);
    }
    return config;
  });

  apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
      const original = error.config as CsrfAxiosConfig | undefined;
      if (
        error.response?.status === 403 &&
        original &&
        !original._csrfRetry &&
        UNSAFE.has((original.method ?? "").toLowerCase())
      ) {
        original._csrfRetry = true;
        await initCsrf();
        if (csrfToken) {
          original.headers.set("X-CSRF-Token", csrfToken);
        }
        return apiClient.request(original);
      }
      return Promise.reject(error);
    }
  );
}
