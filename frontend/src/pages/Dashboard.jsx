// Dashboard.jsx - [MOD] radar + rings + profile bar + shortcuts
// FILE: frontend/src/pages/Dashboard.jsx
// BATCH 25 / v10 Dashboard (new) - The command center, composed:
//   greeting -> [daily ring | profile spectrum] -> [radar | module grid]
//   with the daily nudge as a quiet banner when the backend sends one.
// One orchestrated entrance: cards rise in a 60ms stagger (CSS in
// index.css, disabled under prefers-reduced-motion). REPLACES the
// Placeholder route target from Batch 24.

import React, { useEffect } from "react";
import { Bell, RefreshCw, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import useAuthStore from "../store/authStore";
import useProfileStore from "../store/profileStore";
import DailyRing from "../components/SkillPath/DailyRing";
import SkillRadarWidget from "../components/SkillPath/SkillRadarWidget";
import ProfileBar from "../components/Dashboard/ProfileBar";
import ModuleGrid from "../components/Dashboard/ModuleGrid";
import { Spinner } from "../components/Common";

function greeting() {
  const hour = new Date().getHours();
  if (hour < 5) return "Working late";
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

// What a guest sees before signing up: sample numbers so every widget and
// module is visible. Clicking any module bounces to /login (ProtectedRoute).
const GUEST_RADAR = [
  { skill: "aptitude", score: 72 },
  { skill: "dsa", score: 58 },
  { skill: "core cs", score: 64 },
  { skill: "communication", score: 70 },
  { skill: "projects", score: 55 },
  { skill: "ml basics", score: 45 },
];

const GUEST_PROFILE_BAR = {
  score: 61,
  components: {
    skill_mastery: 65,
    assessment_history: 55,
    coding_strength: 60,
    interview_readiness: 58,
    resume_completeness: 70,
    consistency: 62,
  },
  next: "Create a free account to start building your real score.",
};

const GUEST_MODULES = {
  topics_completed: 12,
  arena_solved: 34,
  studio_sessions: 3,
  resume_documents: 1,
  jobs_saved: 8,
  championships_entered: 2,
};

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.token);
  const isGuest = !token;
  const {
    loading, error, ring, streak, radar, profileBar, modules, nudge,
    componentOrder, load,
  } = useProfileStore();

  useEffect(() => {
    // Guests have no data to load (and no token — the call would 401).
    if (token) load();
  }, [token, load]);

  const firstName =
    (user?.full_name || "").split(" ")[0] || user?.email?.split("@")[0] || "";

  if (!isGuest && loading && !radar.length && !profileBar.score) {
    return (
      <div className="h-full flex items-center justify-center">
        <Spinner size={28} />
      </div>
    );
  }

  // Guests see sample data in every widget so they can explore the whole app.
  const viewRing = isGuest ? { points: 30, goal: 50 } : ring;
  const viewStreak = isGuest ? { days: 5, nextMilestone: 7 } : streak;
  const viewRadar = isGuest ? GUEST_RADAR : radar;
  const viewBar = isGuest
    ? { ...GUEST_PROFILE_BAR, weights: profileBar.weights }
    : profileBar;
  const viewModules = isGuest ? GUEST_MODULES : modules;

  return (
    <div className="p-4 lg:p-6 max-w-6xl mx-auto space-y-4">
      {/* Greeting row */}
      <div className="rise flex items-end justify-between" style={{ "--d": "0ms" }}>
        <div>
          <h1 className="text-2xl font-bold text-gray-50">
            {isGuest ? "Welcome to ATLAS AI." : `${greeting()}${firstName ? `, ${firstName}` : ""}.`}
          </h1>
          <p className="text-sm text-gray-500">
            {isGuest
              ? "Look around freely — this is a live preview with sample data."
              : "Here's where you stand — and the fastest way up."}
          </p>
        </div>
        {!isGuest && (
          <button
            onClick={load}
            title="Refresh"
            className="text-gray-600 hover:text-gray-300 transition p-2"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          </button>
        )}
      </div>

      {isGuest && (
        <div className="rise flex flex-wrap items-center gap-3 rounded-xl border border-cyan-900/60 bg-cyan-950/30 px-4 py-3" style={{ "--d": "40ms" }}>
          <Sparkles size={16} className="text-cyan-400 shrink-0" />
          <p className="text-sm text-cyan-200 flex-1 min-w-[200px]">
            You're browsing as a guest. Open any module to get started — we'll
            ask you to sign in first (Google works in one tap).
          </p>
          <div className="flex items-center gap-2">
            <Link
              to="/register"
              className="px-3 py-1.5 rounded-lg bg-cyan-500 text-gray-950 text-sm font-semibold hover:bg-cyan-400 transition"
            >
              Create free account
            </Link>
            <Link
              to="/login"
              className="px-3 py-1.5 rounded-lg border border-cyan-800 text-cyan-300 text-sm hover:bg-cyan-950 transition"
            >
              Log in
            </Link>
          </div>
        </div>
      )}

      {!isGuest && error && (
        <div className="rise rounded-xl border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300" style={{ "--d": "40ms" }}>
          {error}
        </div>
      )}

      {!isGuest && nudge?.message && (
        <div className="rise flex items-center gap-3 rounded-xl border border-cyan-900/60 bg-cyan-950/30 px-4 py-3" style={{ "--d": "60ms" }}>
          <Bell size={16} className="text-cyan-400 shrink-0" />
          <p className="text-sm text-cyan-200">{nudge.message}</p>
        </div>
      )}

      {/* Standing */}
      <div className="grid lg:grid-cols-5 gap-4">
        <div className="rise lg:col-span-2" style={{ "--d": "120ms" }}>
          <DailyRing
            points={viewRing.points}
            goal={viewRing.goal}
            streakDays={viewStreak.days}
            nextMilestone={viewStreak.nextMilestone}
          />
        </div>
        <div className="rise lg:col-span-3" style={{ "--d": "180ms" }}>
          <ProfileBar
            score={viewBar.score}
            components={viewBar.components}
            weights={viewBar.weights}
            next={viewBar.next}
            order={componentOrder}
          />
        </div>
      </div>

      {/* Detail */}
      <div className="grid lg:grid-cols-5 gap-4">
        <div className="rise lg:col-span-2" style={{ "--d": "240ms" }}>
          <SkillRadarWidget radar={viewRadar} />
        </div>
        <div className="rise lg:col-span-3" style={{ "--d": "300ms" }}>
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500 mb-2">
            {isGuest ? "Explore the modules" : "Your modules"}
          </p>
          <ModuleGrid modules={viewModules} />
        </div>
      </div>
    </div>
  );
}