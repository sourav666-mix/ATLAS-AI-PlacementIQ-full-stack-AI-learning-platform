// Navbar.jsx - top nav
// FILE: frontend/src/components/Layout/Navbar.jsx
// BATCH 24 / v10 Foundation (new) - Top bar: brand, streak flame, points
// today (filled by profileStore later), user menu with logout.

import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Flame, LogOut, User as UserIcon, Menu } from "lucide-react";
import useAuthStore from "../../store/authStore";

export default function Navbar({ onToggleSidebar }) {
  const { user, token, logout } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();
  const isGuest = !token;

  const doLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="h-14 shrink-0 bg-gray-950 border-b border-gray-800 flex items-center justify-between px-4">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden text-gray-400 hover:text-gray-200"
        >
          <Menu size={20} />
        </button>
        <span className="font-bold text-gray-100 tracking-tight">
          ATLAS<span className="text-cyan-400"> AI</span>
        </span>
      </div>

      {isGuest ? (
        <div className="flex items-center gap-2">
          <Link
            to="/login"
            className="px-3 py-1.5 rounded-lg text-sm text-gray-300 hover:text-white border border-gray-800 hover:border-gray-600 transition"
          >
            Log in
          </Link>
          <Link
            to="/register"
            className="px-3 py-1.5 rounded-lg text-sm font-semibold bg-cyan-500 text-gray-950 hover:bg-cyan-400 transition"
          >
            Sign up free
          </Link>
        </div>
      ) : (
      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-1.5 text-sm text-amber-400">
          <Flame size={16} />
          <span className="font-semibold">
            {user?.current_streak ?? 0}
          </span>
        </div>
        <div className="relative">
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="flex items-center gap-2 text-sm text-gray-300 hover:text-white"
          >
            <span className="h-8 w-8 rounded-full bg-cyan-950 text-cyan-300 flex items-center justify-center">
              <UserIcon size={16} />
            </span>
            <span className="hidden sm:inline max-w-[10rem] truncate">
              {user?.full_name || user?.email || "Student"}
            </span>
          </button>
          {menuOpen && (
            <div
              className="absolute right-0 mt-2 w-44 bg-gray-900 border border-gray-800 rounded-xl shadow-xl py-1 z-50"
              onMouseLeave={() => setMenuOpen(false)}
            >
              <button
                onClick={() => { setMenuOpen(false); navigate("/profile"); }}
                className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-800"
              >
                Profile
              </button>
              <button
                onClick={doLogout}
                className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-gray-800 flex items-center gap-2"
              >
                <LogOut size={14} /> Log out
              </button>
            </div>
          )}
        </div>
      </div>
      )}
    </header>
  );
}