import { useCallback, useEffect, useState } from "react";
import { getReact, axiosErrorMessage } from "../api/getReact";

/**
 * Хук: getReact (axios GET) → backend JSON → setState в React.
 *
 * @param path — путь относительно /api, например "/dashboard"
 * @param enabled — если false, запрос не выполняется
 */
export function useGetReact<T>(path: string | null, enabled = true) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(enabled && path));

  const reload = useCallback(async () => {
    if (!path) return;
    setLoading(true);
    setError(null);
    try {
      const json = await getReact<T>(path);
      setData(json);
    } catch (e) {
      setError(axiosErrorMessage(e));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    if (!enabled || !path) {
      setLoading(false);
      return;
    }
    void reload();
  }, [enabled, path, reload]);

  return { data, setData, error, loading, reload };
}
