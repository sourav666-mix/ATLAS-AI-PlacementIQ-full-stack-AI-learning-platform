import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAdminAuthStore } from "../store/adminAuthStore";

export default function AdminLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const signIn = useAdminAuthStore((s) => s.signIn);
  const loading = useAdminAuthStore((s) => s.loading);
  const error = useAdminAuthStore((s) => s.error);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const from = location.state?.from?.pathname || "/dashboard";

  async function handleSubmit(e) {
    e.preventDefault();
    const ok = await signIn(email.trim(), password);
    if (ok) navigate(from, { replace: true });
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm bg-white border border-slate-200 rounded-2xl p-8 shadow-sm">
        <div className="mb-6">
          <div className="font-semibold text-slate-900 text-xl">ATLAS AI</div>
          <div className="text-sm text-slate-500">Admin sign in</div>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-600 mb-1">Email</label>
            {/* type="text" not "email": this account's login value intentionally
                isn't a standard email format, and type="email" would silently
                block submission via the browser's own native validation
                before onSubmit ever fires. */}
            <input type="text" autoComplete="username" value={email}
              onChange={(e) => setEmail(e.target.value)} required
              className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400" />
          </div>
          <div>
            <label className="block text-sm text-slate-600 mb-1">Password</label>
            <input type="password" autoComplete="current-password" value={password}
              onChange={(e) => setPassword(e.target.value)} required
              className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400" />
          </div>
          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</div>
          )}
          <button type="submit" disabled={loading}
            className="w-full py-2.5 rounded-lg bg-slate-900 text-white text-sm font-medium hover:bg-slate-700 disabled:opacity-60">
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}