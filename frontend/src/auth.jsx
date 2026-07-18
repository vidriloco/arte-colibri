// Auth context: current user/role/token, hydrated from /api/auth/me.
import React from "react";
import { Auth, getToken, setToken } from "./api.js";

const AuthContext = React.createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = React.useState(null);
  const [ready, setReady] = React.useState(false);

  const refresh = React.useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      setReady(true);
      return null;
    }
    try {
      const me = await Auth.me();
      setUser(me);
      return me;
    } catch {
      setToken(null);
      setUser(null);
      return null;
    } finally {
      setReady(true);
    }
  }, []);

  React.useEffect(() => {
    refresh();
  }, [refresh]);

  const applyAuth = React.useCallback((payload) => {
    // payload = { token, user }
    setToken(payload.token);
    setUser(payload.user);
    return payload.user;
  }, []);

  const login = React.useCallback(
    async (email, password) => applyAuth(await Auth.login({ email, password })),
    [applyAuth]
  );

  const signup = React.useCallback(
    async (body) => applyAuth(await Auth.signup(body)),
    [applyAuth]
  );

  const logout = React.useCallback(async () => {
    try {
      await Auth.logout();
    } catch {
      /* ignore */
    }
    setToken(null);
    setUser(null);
  }, []);

  const value = React.useMemo(
    () => ({ user, ready, role: user?.role || null, login, signup, logout, refresh, setUser }),
    [user, ready, login, signup, logout, refresh]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return React.useContext(AuthContext);
}
