import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useMutation } from "urql";

import { Button, ErrorNote, Field, Input } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { LOGIN, REGISTER } from "../gql/operations";

type AuthResult = { token: string; user: { id: string; email: string } };

export default function AuthPage({ mode }: { mode: "login" | "register" }) {
  const isLogin = mode === "login";
  const navigate = useNavigate();
  const { token, signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [{ fetching }, run] = useMutation<
    { login: AuthResult } | { register: AuthResult }
  >(isLogin ? LOGIN : REGISTER);
  const [error, setError] = useState<string | null>(null);

  if (token) return <Navigate to="/" replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const res = await run({ email, password });
    if (res.error) {
      setError(res.error.graphQLErrors[0]?.message ?? res.error.message);
      return;
    }
    const payload = isLogin
      ? (res.data as { login: AuthResult }).login
      : (res.data as { register: AuthResult }).register;
    signIn(payload.token);
    navigate("/", { replace: true });
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="text-3xl">🍕</div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">pizza</h1>
          <p className="mt-1 text-sm text-slate-500">Slice up your paycheck.</p>
        </div>
        <form
          onSubmit={onSubmit}
          className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <h2 className="text-lg font-semibold">
            {isLogin ? "Welcome back" : "Create your account"}
          </h2>
          <Field label="Email">
            <Input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </Field>
          <Field label="Password" hint={isLogin ? undefined : "At least 8 characters."}>
            <Input
              type="password"
              required
              autoComplete={isLogin ? "current-password" : "new-password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </Field>
          <ErrorNote>{error}</ErrorNote>
          <Button type="submit" className="w-full" disabled={fetching}>
            {fetching ? "Please wait…" : isLogin ? "Sign in" : "Create account"}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          {isLogin ? "No account yet? " : "Already have an account? "}
          <Link
            to={isLogin ? "/register" : "/login"}
            className="font-medium text-amber-700 hover:underline"
          >
            {isLogin ? "Sign up" : "Sign in"}
          </Link>
        </p>
      </div>
    </div>
  );
}
