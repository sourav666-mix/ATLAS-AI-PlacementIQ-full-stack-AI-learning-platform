// FILE: frontend/src/components/Dashboard/ModuleGrid.jsx
// BATCH 25 / v10 Dashboard (new) - Module shortcuts with LIVE counters from
// the dashboard payload. Each tile: icon, count, one plain-verb label.

import React from "react";
import { useNavigate } from "react-router-dom";
import {
  Code2, Briefcase, Trophy, Mic, FileText, BookOpen, FlaskConical, Sparkles,
} from "lucide-react";

const TILES = [
  { key: "topics_completed", label: "Topics completed", icon: BookOpen, to: "/roadmap", color: "#22d3ee" },
  { key: "arena_solved", label: "Problems solved", icon: Code2, to: "/arena", color: "#34d399" },
  { key: "studio_sessions", label: "Mock interviews", icon: Mic, to: "/studio", color: "#fbbf24" },
  { key: "resume_documents", label: "Resumes built", icon: FileText, to: "/resume", color: "#f472b6" },
  { key: "jobs_saved", label: "Jobs saved", icon: Briefcase, to: "/jobs", color: "#a78bfa" },
  { key: "championships_entered", label: "Championships", icon: Trophy, to: "/championship", color: "#fb923c" },
  { key: "_labs", label: "Live Lab", icon: FlaskConical, to: "/labs", color: "#38bdf8", static: "Open" },
  { key: "_mlviz", label: "ML intuition", icon: Sparkles, to: "/ml-viz", color: "#e879f9", static: "Play" },
];

export default function ModuleGrid({ modules = {} }) {
  const navigate = useNavigate();
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {TILES.map(({ key, label, icon: Icon, to, color, static: staticText }) => (
        <button
          key={key}
          onClick={() => navigate(to)}
          className="group bg-gray-900 border border-gray-800 rounded-2xl p-4 text-left transition hover:border-gray-600 hover:-translate-y-0.5 focus-visible:ring-2 focus-visible:ring-cyan-400 outline-none"
        >
          <Icon size={18} style={{ color }} />
          <p className="mt-3 text-2xl font-bold text-gray-50 tabular-nums leading-none">
            {staticText || Number(modules[key] ?? 0)}
          </p>
          <p className="mt-1 text-[11px] text-gray-500 group-hover:text-gray-400">
            {label}
          </p>
        </button>
      ))}
    </div>
  );
}