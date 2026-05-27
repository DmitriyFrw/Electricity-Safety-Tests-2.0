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

export function axiosErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const ax = err as AxiosError<{ detail?: string }>;
    const detail = ax.response?.data?.detail;
    if (typeof detail === "string") return detail;
    return ax.message;
  }
  if (err instanceof Error) return err.message;
  return "Ошибка запроса";
}
