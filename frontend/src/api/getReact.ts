import { apiClient, axiosCorrelationId, axiosErrorCode, axiosErrorMessage } from "./axios";

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

/** GET бинарного ответа (файл) и сохранение на диск. */
export async function downloadReact(path: string, fallbackFilename: string): Promise<void> {
  const response = await apiClient.get<Blob>(path, { responseType: "blob" });
  const disposition = response.headers["content-disposition"] as string | undefined;
  const match = disposition?.match(/filename="?([^";]+)"?/i);
  const filename = match?.[1] ?? fallbackFilename;
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export { axiosCorrelationId, axiosErrorCode, axiosErrorMessage };
