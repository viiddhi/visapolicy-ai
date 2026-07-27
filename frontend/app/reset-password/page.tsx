"use client";
import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { resetPassword } from "@/lib/api";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords don't match.");
      return;
    }
    if (!token) {
      setError("Missing reset token — use the link from your email.");
      return;
    }

    setLoading(true);
    try {
      await resetPassword(token, password);
      setDone(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-brand">
            Visapolicy<span className="text-brand-light">.ai</span>
          </h1>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
          {!token ? (
            <div className="text-center py-2">
              <p className="text-sm font-medium text-gray-900 mb-1">Invalid reset link</p>
              <p className="text-sm text-gray-500">
                This link is missing its reset token. Request a new one from the sign-in page.
              </p>
              <button
                onClick={() => router.push("/")}
                className="mt-6 text-sm text-brand-light font-medium hover:underline"
              >
                ← Back to sign in
              </button>
            </div>
          ) : done ? (
            <div className="text-center py-2">
              <p className="text-2xl mb-3">✓</p>
              <p className="text-sm font-medium text-gray-900 mb-1">Password updated</p>
              <p className="text-sm text-gray-500 mb-6">You can now sign in with your new password.</p>
              <button
                onClick={() => router.push("/")}
                className="w-full bg-brand text-white rounded-lg py-2.5 text-sm font-medium hover:bg-opacity-90 transition"
              >
                Go to sign in
              </button>
            </div>
          ) : (
            <form onSubmit={submit} className="space-y-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-1">Set a new password</h2>
                <p className="text-sm text-gray-500 mb-4">Choose a new password for your account.</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">New password</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-light"
                  placeholder="••••••••"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Confirm new password</label>
                <input
                  type="password"
                  required
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-light"
                  placeholder="••••••••"
                />
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-brand text-white rounded-lg py-2.5 text-sm font-medium hover:bg-opacity-90 transition disabled:opacity-60"
              >
                {loading ? "Updating…" : "Update password"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordForm />
    </Suspense>
  );
}
