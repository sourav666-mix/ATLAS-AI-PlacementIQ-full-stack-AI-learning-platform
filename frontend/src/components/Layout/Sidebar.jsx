// Sidebar.jsx - side nav
// FILE: frontend/src/components/Layout/Sidebar.jsx
// BATCH 24 / v10 Foundation (new) - Left nav. Links cover every route the
// student app will have (v10 modules + the v11 Live Lab / ML Viz). Pages
// arrive in later batches; the links are here so the shell is complete and
// each batch just fills in a screen.
// V12 FIX (this revision):
//   * SkillPath tagged "v12" - it now opens the reforged domain-first flow
//     (/skillpath -> plan -> roadmap -> learn -> practice). NavLink's
//     default partial matching keeps it highlighted across all sub-steps.
//   * "My Roadmap" (/roadmap) added - the legacy v10 SkillPathRoadmap route
//     existed in App.jsx but had no sidebar link (orphaned page).
//   * "Career Target" (/career) added - the v12 Career Target & Gap Engine.
//     Placed directly under Dashboard because it is diagnostic-first: it tells
//     the student "am I ready / what do I fix" and every action it produces
//     routes into the modules below it.
// Nothing removed.

import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Target, Route as RouteIcon, Map, BookOpen, Code2, Dumbbell,
  FileText, Briefcase, Trophy, Medal, Mic, Building2, ClipboardList,
  FlaskConical, Sparkles, User, Beaker,
} from "lucide-react";

const LINKS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/career", label: "Career Target", icon: Target, tag: "v12" },
  { to: "/skillpath", label: "SkillPath", icon: RouteIcon, tag: "v12" },
 // { to: "/roadmap", label: "My Roadmap", icon: Map },
 //{ to: "/learn", label: "Topic Learning", icon: BookOpen },
  { to: "/arena", label: "Code Arena", icon: Code2 },
  { to: "/dsa", label: "DSA Gym", icon: Dumbbell },
  { to: "/labs", label: "Live Lab", icon: FlaskConical, tag: "v11" },
  { to: "/labpro", label: "Live Lab Pro", icon: Beaker, tag: "v12" },
  { to: "/ml-viz", label: "ML Intuition", icon: Sparkles, tag: "v11" },
  { to: "/resume", label: "Resume AI", icon: FileText },
  { to: "/assessment", label: "Assessment", icon: ClipboardList },
  { to: "/company", label: "Company Intel", icon: Building2 },
  { to: "/jobs", label: "Jobs Board", icon: Briefcase },
  { to: "/championship", label: "Championship", icon: Trophy },
  { to: "/leaderboard", label: "Leaderboard", icon: Medal },
  { to: "/studio", label: "Interview Studio", icon: Mic },
  { to: "/profile", label: "Profile", icon: User },
];

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={`fixed lg:static z-40 top-0 left-0 h-full w-60 bg-gray-950 border-r border-gray-800 overflow-y-auto transition-transform ${
          open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <nav className="p-3 space-y-1">
          {LINKS.map(({ to, label, icon: Icon, tag }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                  isActive
                    ? "bg-cyan-950/60 text-cyan-300"
                    : "text-gray-400 hover:bg-gray-900 hover:text-gray-200"
                }`
              }
            >
              <Icon size={18} />
              <span className="flex-1">{label}</span>
              {tag && (
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-gray-800 text-cyan-400">
                  {tag}
                </span>
              )}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
}