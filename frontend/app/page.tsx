"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, register, forgotPassword, ApiError } from "@/lib/api";
import { saveToken } from "@/lib/auth";

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register" | "forgot">("login");
  const [form, setForm] = useState({ email: "", password: "", name: "" });
  const [error, setError] = useState("");
  const [alreadyRegistered, setAlreadyRegistered] = useState(false);
  const [loading, setLoading] = useState(false);
  const [forgotSent, setForgotSent] = useState(false);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setAlreadyRegistered(false);
    setLoading(true);
    try {
      const res =
        mode === "login"
          ? await login(form.email, form.password)
          : await register(form.email, form.password, form.name);
      saveToken(res.access_token);
      router.push(mode === "register" ? "/onboarding" : "/dashboard");
    } catch (err: unknown) {
      if (mode === "register" && err instanceof ApiError && err.status === 409) {
        setAlreadyRegistered(true);
      } else {
        setError(err instanceof Error ? err.message : "Something went wrong");
      }
    } finally {
      setLoading(false);
    }
  }

  async function submitForgot(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await forgotPassword(form.email);
      setForgotSent(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  function goToForgot() {
    setMode("forgot");
    setError("");
    setAlreadyRegistered(false);
    setForgotSent(false);
  }

  function backToLogin() {
    setMode("login");
    setError("");
    setAlreadyRegistered(false);
    setForgotSent(false);
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-brand">
            Visapolicy<span className="text-brand-light">.ai</span>
          </h1>
          <p className="mt-2 text-gray-500 text-sm">
            Real-time USCIS rule change alerts — personalized to your visa status
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
          {mode !== "forgot" && (
            <div className="flex rounded-lg bg-gray-100 p-1 mb-6">
              {(["login", "register"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => { setMode(m); setError(""); setAlreadyRegistered(false); }}
                  className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                    mode === m ? "bg-white shadow text-gray-900" : "text-gray-500"
                  }`}
                >
                  {m === "login" ? "Sign in" : "Create account"}
                </button>
              ))}
            </div>
          )}

          {mode === "forgot" ? (
            forgotSent ? (
              <div className="text-center py-2">
                <p className="text-2xl mb-3">✓</p>
                <p className="text-sm font-medium text-gray-900 mb-1">Check your email</p>
                <p className="text-sm text-gray-500">
                  If an account exists for <span className="font-medium">{form.email}</span>, we've sent a link to
                  reset your password. It expires in 1 hour.
                </p>
                <button
                  onClick={backToLogin}
                  className="mt-6 text-sm text-brand-light font-medium hover:underline"
                >
                  ← Back to sign in
                </button>
              </div>
            ) : (
              <form onSubmit={submitForgot} className="space-y-4">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 mb-1">Reset your password</h2>
                  <p className="text-sm text-gray-500 mb-4">
                    Enter your account email and we'll send you a link to reset your password.
                  </p>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
                  <input
                    type="email"
                    required
                    value={form.email}
                    onChange={set("email")}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-light"
                    placeholder="you@example.com"
                  />
                </div>
                {error && <p className="text-sm text-red-600">{error}</p>}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-brand text-white rounded-lg py-2.5 text-sm font-medium hover:bg-opacity-90 transition disabled:opacity-60"
                >
                  {loading ? "Sending…" : "Send reset link"}
                </button>
                <button
                  type="button"
                  onClick={backToLogin}
                  className="w-full text-sm text-gray-500 hover:text-gray-700 text-center"
                >
                  ← Back to sign in
                </button>
              </form>
            )
          ) : (
            <form onSubmit={submit} className="space-y-4">
              {mode === "register" && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full name</label>
                  <input
                    type="text"
                    required
                    value={form.name}
                    onChange={set("name")}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-light"
                    placeholder="Vidhi Patel"
                  />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
                <input
                  type="email"
                  required
                  value={form.email}
                  onChange={set("email")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-light"
                  placeholder="you@example.com"
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium text-gray-700">Password</label>
                  {mode === "login" && (
                    <button
                      type="button"
                      onClick={goToForgot}
                      className="text-xs text-brand-light font-medium hover:underline"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <input
                  type="password"
                  required
                  minLength={mode === "register" ? 8 : undefined}
                  value={form.password}
                  onChange={set("password")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-light"
                  placeholder="••••••••"
                />
                {mode === "register" && (
                  <p className="text-xs text-gray-400 mt-1">At least 8 characters, with letters and numbers</p>
                )}
              </div>
              {alreadyRegistered && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2.5">
                  <p className="text-sm text-amber-800">
                    This email is already registered.{" "}
                    <button
                      type="button"
                      onClick={goToForgot}
                      className="font-medium underline hover:no-underline"
                    >
                      Reset your password
                    </button>{" "}
                    instead?
                  </p>
                </div>
              )}
              {error && <p className="text-sm text-red-600">{error}</p>}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-brand text-white rounded-lg py-2.5 text-sm font-medium hover:bg-opacity-90 transition disabled:opacity-60"
              >
                {loading ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
