// FILE: frontend/src/pages/Login.jsx
// BATCH 24 / v10 Foundation (new) - Email/password login. On success the
// authStore holds the token+user and we go to the dashboard.

import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import useAuthStore from "../store/authStore";
import { Button, Spinner } from "../components/Common";
import GoogleSignInButton from "../components/Auth/GoogleSignInButton";

export default function Login() {
  const { login, loading, error } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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

  const submit = async () => {
    const ok = await login(email.trim(), password);
    if (ok) goBack();
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold">
            ATLAS<span className="text-cyan-400"> AI</span>
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Your placement-prep command center.
          </p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-cyan-700"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-cyan-700"
          />
          {error && <p className="text-xs text-red-400">{error}</p>}
          <Button onClick={submit} full disabled={loading}>
            {loading ? <Spinner size={16} /> : "Log in"}
          </Button>
          <GoogleSignInButton onSuccess={goBack} />
        </div>

        <p className="text-center text-sm text-gray-500">
          New here?{" "}
          <Link
            to={`/register?next=${encodeURIComponent(from)}`}
            className="text-cyan-400 hover:underline"
          >
            Create an account
          </Link>
        </p>

        <p className="text-center text-xs text-gray-600">
          <Link to="/dashboard" className="hover:text-gray-400 hover:underline">
            ← Just looking? Browse the dashboard as a guest
          </Link>
        </p>
      </div>
    </div>
  );
}