// NudgeBadge.jsx - [NEW] daily proactive nudge badge
// FILE: frontend/src/components/GlobalAssistant/NudgeBadge.jsx
// BATCH 28 / v10 Global Assistant (new) - The proactive nudge: a small
// dismissible bubble above the assistant button. Max ONE per day (backend
// enforces; the client also remembers today's dismissal in localStorage so
// it doesn't reappear after a route change). Hidden during a live exam.

import React, { useEffect, useState } from "react";
import { X } from "lucide-react";
import useProfileStore from "../../store/profileStore";
import useTutorStore from "../../store/tutorStore";

function dismissedToday() {
  try {
    return localStorage.getItem("atlas_nudge_dismissed") ===
      new Date().toISOString().slice(0, 10);
  } catch (_) {
    return false;
  }
}

export default function NudgeBadge() {
  const nudge = useProfileStore((s) => s.nudge);
  const { locked, toggle } = useTutorStore();
  const [hidden, setHidden] = useState(dismissedToday());

  useEffect(() => {
    setHidden(dismissedToday());
  }, [nudge]);

  if (locked || hidden || !nudge?.message) return null;

  const dismiss = (e) => {
    e.stopPropagation();
    try {
      localStorage.setItem(
        "atlas_nudge_dismissed",
        new Date().toISOString().slice(0, 10)
      );
    } catch (_) {
      /* ignore */
    }
    setHidden(true);
  };

  return (
    <button
      onClick={() => { toggle(); dismiss({ stopPropagation() {} }); }}
      className="fixed bottom-24 right-5 z-30 max-w-[16rem] text-left rounded-2xl rounded-br-sm bg-gray-900 border border-cyan-900/70 shadow-xl px-3.5 py-2.5 pr-8 hover:border-cyan-700 transition"
    >
      <span className="block text-xs text-cyan-200 leading-relaxed">
        {nudge.message}
      </span>
      <span
        onClick={dismiss}
        className="absolute top-1.5 right-1.5 text-gray-500 hover:text-gray-300 p-1"
      >
        <X size={12} />
      </span>
    </button>
  );
}