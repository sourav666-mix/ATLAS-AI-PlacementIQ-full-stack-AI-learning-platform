// FILE: admin-panel/src/components/Layout/AdminShell.jsx
// BATCH 32 / Admin Panel (new) - The admin shell: top bar + role-aware nav.
// Super-admin-only areas (Colleges, Revenue, Providers) are hidden from a
// college_admin — the server enforces this too, but the UI shouldn't tease
// links a college admin can't use.

import React, { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, BookOpen, Briefcase, Trophy, Building2, Users,
  BarChart3, Server, LogOut, Menu, ShieldCheck,
} from "lucide-react";
import useAdminAuthStore from "../../store/adminAuthStore";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/content", label: "Content", icon: BookOpen },
  { to: "/jobs", label: "Jobs", icon: Briefcase },
  { to: "/championships", label: "Championships", icon: Trophy },
  { to: "/students", label: "Students", icon: Users },
  { to: "/colleges", label: "Colleges", icon: Building2, superOnly: true },
  { to: "/revenue", label: "Revenue", icon: BarChart3, superOnly: true },
  { to: "/providers", label: "AI Providers", icon: Server, superOnly: true },
];

export default function AdminShell({ children }) {
  const { admin, isSuper, logout } = useAdminAuthStore();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const links = NAV.filter((n) => !n.superOnly || isSuper);

  return (
    <div className="h-screen flex flex-col bg-gray-950 text-gray-100">
      <header className="h-14 shrink-0 border-b border-gray-800 flex items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <button onClick={() => setOpen((v) => !v)} className="lg:hidden text-gray-400"><Menu size={20} /></button>
          <span className="font-bold tracking-tight flex items-center gap-2">
            <ShieldCheck size={18} className="text-violet-400" />
            ATLAS<span className="text-violet-400"> Admin</span>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500 capitalize hidden sm:inline">
            {(admin?.role || "").replace("_", " ")}{admin?.college_name ? ` · ${admin.college_name}` : ""}
          </span>
          <button onClick={() => { logout(); navigate("/login"); }} className="text-red-400 hover:text-red-300 flex items-center gap-1.5 text-sm">
            <LogOut size={15} /> <span className="hidden sm:inline">Log out</span>
          </button>
        </div>
      </header>

      <div className="flex-1 flex min-h-0">
        {open && <div className="fixed inset-0 bg-black/50 z-30 lg:hidden" onClick={() => setOpen(false)} />}
        <aside className={`fixed lg:static z-40 top-0 left-0 h-full w-56 bg-gray-950 border-r border-gray-800 overflow-y-auto transition-transform ${open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}>
          <nav className="p-3 space-y-1">
            {links.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} onClick={() => setOpen(false)}
                className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${isActive ? "bg-violet-950/60 text-violet-300" : "text-gray-400 hover:bg-gray-900 hover:text-gray-200"}`}>
                <Icon size={18} /> {label}
              </NavLink>
            ))}
          </nav>
        </aside>
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}