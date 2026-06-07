import { apiClient, axiosErrorMessage } from "./axios";

/**
 * GET к backend → JSON → возвращает типизированные данные для React state.
 * Пример: const dashboard = await getReact<Dashboard>("/dashboard");
 */
export async function getReact<T>(path: string): Promise<T> {
  const { data } = await apiClient.get<T>(path);
  return data;
}

/** POST: тело JSON, ответ JSON. */
export async function postReact<T>(path: string, body?: unknown): Promise<T> {
  const { data } = await apiClient.post<T>(path, body);
  return data;
}

/** PUT */
export async function putReact<T>(path: string, body?: unknown): Promise<T> {
  const { data } = await apiClient.put<T>(path, body);
  return data;
}

/** DELETE */
export async function deleteReact<T>(path: string): Promise<T> {
  const { data } = await apiClient.delete<T>(path);
  return data;
}

/** POST multipart/form-data */
export async function postFormReact<T>(path: string, body: FormData): Promise<T> {
  const { data } = await apiClient.post<T>(path, body, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export { axiosErrorMessage };
