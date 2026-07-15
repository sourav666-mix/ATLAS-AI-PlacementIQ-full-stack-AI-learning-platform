// FILE: frontend/src/pages/Register.jsx
// BATCH 24 / v10 Foundation (new) - Create account -> auto-login -> dashboard.
// Sends full_name/email/password; the store falls back through login.

import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import useAuthStore from "../store/authStore";
import { Button, Spinner } from "../components/Common";
import GoogleSignInButton from "../components/Auth/GoogleSignInButton";

export default function Register() {
  const { register, loading, error } = useAuthStore();
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [localError, setLocalError] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();
  // Where the guest was headed when ProtectedRoute bounced them here
  // (?next= from ProtectedRoute; state.from kept as a fallback). Only
  // internal paths are honored so ?next= can't redirect off-site.
  const rawNext =
    new URLSearchParams(location.search).get("next") ||
    location.state?.from ||
    "/dashboard";
  const from = rawNext.startsWith("/") ? rawNext : "/dashboard";

  const goBack = () => navigate(from, { replace: true });

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async () => {
    setLocalError(null);
    if (form.password.length < 8) {
      setLocalError("Password must be at least 8 characters.");
      return;
    }
    const ok = await register({
      full_name: form.full_name.trim(),
      email: form.email.trim(),
      password: form.password,
    });
    if (ok) goBack();
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold">
            ATLAS<span className="text-cyan-400"> AI</span>
          </h1>
          <p className="text-sm text-gray-400 mt-1">Create your account.</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-4">
          <input
            placeholder="Full name"
            value={form.full_name}
            onChange={set("full_name")}
            className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-cyan-700"
          />
          <input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={set("email")}
            className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-cyan-700"
          />
          <input
            type="password"
            placeholder="Password (min 8 chars)"
            value={form.password}
            onChange={set("password")}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-cyan-700"
          />
          {(localError || error) && (
            <p className="text-xs text-red-400">{localError || error}</p>
          )}
          <Button onClick={submit} full disabled={loading}>
            {loading ? <Spinner size={16} /> : "Create account"}
          </Button>
          <GoogleSignInButton onSuccess={goBack} />
        </div>

        <p className="text-center text-sm text-gray-500">
          Already have an account?{" "}
          <Link
            to={`/login?next=${encodeURIComponent(from)}`}
            className="text-cyan-400 hover:underline"
          >
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}