import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useQuery } from "urql";

import { ME } from "../gql/operations";
import { clearToken, getToken, setToken } from "../lib/auth";

type User = { id: string; email: string };

type AuthState = {
  token: string | null;
  user: User | null;
  initializing: boolean;
  signIn: (token: string) => void;
  signOut: () => void;
};

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => getToken());

  const [{ data, fetching, error }] = useQuery<{ me: User }>({
    query: ME,
    pause: !token,
    requestPolicy: "cache-and-network",
  });

  useEffect(() => {
    if (token && error) {
      clearToken();
      setTokenState(null);
    }
  }, [token, error]);

  const value = useMemo<AuthState>(
    () => ({
      token,
      user: token ? (data?.me ?? null) : null,
      initializing: Boolean(token) && fetching && !data,
      signIn: (t: string) => {
        setToken(t);
        setTokenState(t);
      },
      signOut: () => {
        clearToken();
        setTokenState(null);
      },
    }),
    [token, data, fetching],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
