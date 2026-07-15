// FILE: frontend/src/App.jsx
// BATCH 24 / v10 Foundation - Router + app shell.
// BATCH 28 - GlobalAssistant mounted OUTSIDE <Routes>.
// GUEST PREVIEW - /dashboard is PUBLIC and lives inside the app shell so a
// guest can land, look around the whole overview (Dashboard renders sample
// data when there's no token), and only gets bounced to /login when they
// open an actual module.
// V12 FIX (this revision) - scroll reset on navigation: the app scrolls
// inside <main class="overflow-y-auto">, NOT the window, so React Router
// never resets it. AppLayout now scrolls the container to top whenever the
// pathname changes (deep pages like TopicLearn -> PracticeArena no longer
// inherit a stale scroll offset). Nothing removed.

import React, { useEffect, useRef, useState } from "react";
import {
  BrowserRouter, Routes, Route, Navigate, Outlet, useLocation,
} from "react-router-dom";
import useAuthStore from "./store/authStore";
import Navbar from "./components/Layout/Navbar";
import Sidebar from "./components/Layout/Sidebar";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import SkillPathRoadmap from "./pages/SkillPathRoadmap";
import DomainSelection from "./pages/SkillPath/DomainSelection";
import PlanSelection from "./pages/SkillPath/PlanSelection";
import RoadmapView from "./pages/SkillPath/RoadmapView";
import TopicLearn from "./pages/SkillPath/TopicLearn";
import PracticeArena from "./pages/SkillPath/PracticeArena";
import RoadmapDashboardPage from "./pages/RoadmapDashboard";
import TopicLearning from "./pages/TopicLearning";
import CodeArena from "./pages/CodeArena";
import DSAGym from "./pages/DSAGym";
import GlobalAssistantButton from "./components/GlobalAssistant/GlobalAssistantButton";
import GlobalAssistantPanel from "./components/GlobalAssistant/GlobalAssistantPanel";
import NudgeBadge from "./components/GlobalAssistant/NudgeBadge";
import ResumeAI from "./pages/ResumeAI";
import JobsBoard from "./pages/JobsBoard";
import Championship from "./pages/Championship";
import Leaderboard from "./pages/Leaderboard";
import InterviewStudio from "./pages/InterviewStudio";
import AssessmentCenter from "./pages/AssessmentCenter";
import CompanyIntel from "./pages/CompanyIntel";
import Profile from "./pages/Profile";
import LiveLab from "./pages/LiveLab";
import LiveLabPro from "./pages/LiveLabPro";
import MLVizBoard from "./components/MLViz/MLVizBoard";
import CareerTarget from "./pages/CareerTarget";
// No token -> send to /login, but remember where they were headed so the
// login screen can return them there after sign-in (Login honors ?next=).
function ProtectedRoute() {
  const token = useAuthStore((s) => s.token);
  const location = useLocation();
  if (!token) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?next=${next}`} replace />;
  }
  return <Outlet />;
}

function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const mainRef = useRef(null);
  const { pathname } = useLocation();

  // V12 FIX: the scroll container is <main>, not the window - reset it on
  // every route change so each page opens at the top.
  useEffect(() => {
    if (mainRef.current) {
      mainRef.current.scrollTo({ top: 0, left: 0, behavior: "instant" });
    }
  }, [pathname]);

  return (
    <div className="h-screen flex flex-col bg-gray-950 text-gray-100">
      <Navbar onToggleSidebar={() => setSidebarOpen((v) => !v)} />
      <div className="flex-1 flex min-h-0">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main ref={mainRef} className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

// Temporary stand-in for screens that arrive in later batches.
function Placeholder({ title }) {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-100">{title}</h1>
      <p className="text-sm text-gray-500 mt-2">
        This screen is coming in an upcoming batch. The route, shell, and auth
        all work — the module UI plugs in here.
      </p>
    </div>
  );
}

// Floating assistant on every authed route; hidden on /login and /register
// and whenever unauthenticated — so guests browsing the dashboard don't see it.
function GlobalAssistantGate() {
  const { pathname } = useLocation();
  const token = useAuthStore((s) => s.token);
  if (!token) return null;
  if (pathname.startsWith("/login") || pathname.startsWith("/register")) {
    return null;
  }
  return (
    <>
      <NudgeBadge />
      <GlobalAssistantPanel />
      <GlobalAssistantButton />
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* App shell wraps BOTH the public dashboard and the gated modules. */}
        <Route element={<AppLayout />}>
          {/* PUBLIC preview — guests land here and can look around freely. */}
          <Route path="/dashboard" element={<Dashboard />} />

          {/* Everything past the dashboard requires an account. A guest who
              opens any module is bounced to /login by ProtectedRoute — the
              "look freely, sign in to use it" flow. */}
          <Route element={<ProtectedRoute />}>
            {/* v12 SkillPath Reforged - the locked 8-step flow */}
            <Route path="/skillpath" element={<DomainSelection />} />
            <Route path="/skillpath/plan/:domainKey" element={<PlanSelection />} />
            <Route path="/skillpath/roadmap/:domainId" element={<RoadmapView />} />
            <Route path="/skillpath/topic/:topicId/learn" element={<TopicLearn />} />
            <Route path="/skillpath/topic/:topicId/practice" element={<PracticeArena />} />
            <Route path="/roadmap/:domainId" element={<RoadmapDashboardPage />} />
            <Route path="/roadmap" element={<SkillPathRoadmap />} />
            <Route path="/learn" element={<TopicLearning />} />
            <Route path="/learn/:topicId" element={<TopicLearning />} />
            <Route path="/arena" element={<CodeArena />} />
            <Route path="/dsa" element={<DSAGym />} />
            <Route path="/labs" element={<LiveLab />} />
            {/* v12 Live Lab Pro - both entry points */}
            <Route path="/labpro" element={<LiveLabPro />} />
            <Route path="/labpro/:sessionId" element={<LiveLabPro />} />
            <Route path="/ml-viz" element={<MLVizBoard />} />
            <Route path="/resume" element={<ResumeAI />} />
            <Route path="/assessment" element={<AssessmentCenter />} />
            <Route path="/company" element={<CompanyIntel />} />
            <Route path="/jobs" element={<JobsBoard />} />
            <Route path="/championship" element={<Championship />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="/studio" element={<InterviewStudio />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/career" element={<CareerTarget />} />
          </Route>
        </Route>

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
      {/* Global Assistant — present on every authed page, outside <Routes> */}
      <GlobalAssistantGate />
    </BrowserRouter>
  );
}