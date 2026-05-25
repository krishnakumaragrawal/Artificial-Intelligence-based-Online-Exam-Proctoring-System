import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { api, TokenResponse, UserPublic } from "../api/client";

const STORAGE_KEY = "proctoring_auth";

interface AuthState {
  token: string | null;
  user: UserPublic | null;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStoredAuth(): AuthState {
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return { token: null, user: null };
  }
  try {
    return JSON.parse(raw) as AuthState;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return { token: null, user: null };
  }
}

function persistAuth(response: TokenResponse): AuthState {
  const state = { token: response.access_token, user: response.user };
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  return state;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(() => readStoredAuth());

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      login: async (email: string, password: string) => {
        const response = await api.login({ email, password });
        setState(persistAuth(response));
      },
      signup: async (email: string, username: string, password: string) => {
        const response = await api.signup({ email, username, password });
        setState(persistAuth(response));
      },
      logout: () => {
        window.localStorage.removeItem(STORAGE_KEY);
        setState({ token: null, user: null });
      }
    }),
    [state]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
