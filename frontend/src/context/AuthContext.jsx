import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";

import * as authApi from "../api/auth";
import { configureAuth, refreshAccessToken } from "../api/client";

const AuthContext = createContext(null);

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem("tf_user") || "null");
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readStoredUser);
  const [ready, setReady] = useState(false);
  const accessTokenRef = useRef(localStorage.getItem("tf_access_token"));

  const persistSession = useCallback((data) => {
    accessTokenRef.current = data.access_token;
    localStorage.setItem("tf_access_token", data.access_token);
    localStorage.setItem("tf_refresh_token", data.refresh_token);
    localStorage.setItem("tf_user", JSON.stringify(data.user));
    setUser(data.user);
  }, []);

  const clearSession = useCallback(() => {
    accessTokenRef.current = null;
    localStorage.removeItem("tf_access_token");
    localStorage.removeItem("tf_refresh_token");
    localStorage.removeItem("tf_user");
    setUser(null);
  }, []);

  useEffect(() => {
    configureAuth({
      getAccessToken: () => accessTokenRef.current,
      persistSession,
      clearSession
    });
    setReady(true);
  }, [persistSession, clearSession]);

  const login = useCallback(async (payload) => {
    const data = await authApi.login(payload);
    persistSession(data);
    return data;
  }, [persistSession]);

  const register = useCallback(async (payload) => {
    const data = await authApi.register(payload);
    persistSession(data);
    return data;
  }, [persistSession]);

  const logout = useCallback(async () => {
    const refreshToken = localStorage.getItem("tf_refresh_token");
    try {
      if (refreshToken) {
        await authApi.logout(refreshToken);
      }
    } catch {
      // Local logout still proceeds if the server rejects a stale token.
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const deleteAccount = useCallback(async () => {
    await authApi.deleteAccount();
    clearSession();
  }, [clearSession]);

  const getAccessToken = useCallback(() => accessTokenRef.current, []);

  const value = useMemo(
    () => ({
      user,
      ready,
      login,
      register,
      logout,
      deleteAccount,
      getAccessToken,
      refreshAccessToken
    }),
    [user, ready, login, register, logout, deleteAccount, getAccessToken]
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
