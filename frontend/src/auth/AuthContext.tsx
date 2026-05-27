import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";
import { getReact } from "../api/getReact";
import type { User } from "../types/api";

interface AuthState {
  user: User | null;
  loading: boolean;
  refresh: () => Promise<void>;
  setUser: (u: User | null) => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const json = await getReact<User | null>("/auth/me");
      setUser(json);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Централизованная обработка ошибок авторизации из axios interceptor.
  useEffect(() => {
    const onAuthError = (_e: Event) => {
      setUser(null);
      navigate("/login");
    };

    const onServerError = (_e: Event) => {
      // На данный момент просто пишем в консоль; можно расширить до toast/notification.
      // eslint-disable-next-line no-console
      console.error("Server error (see network/details).");
    };

    window.addEventListener("auth-error", onAuthError);
    window.addEventListener("server-error", onServerError);
    return () => {
      window.removeEventListener("auth-error", onAuthError);
      window.removeEventListener("server-error", onServerError);
    };
  }, [navigate]);

  const value = useMemo(
    () => ({ user, loading, refresh, setUser }),
    [user, loading, refresh]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside AuthProvider");
  return ctx;
}
