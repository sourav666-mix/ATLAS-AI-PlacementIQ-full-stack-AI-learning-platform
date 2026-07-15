// GlobalAssistantButton.jsx - [MOD] floating button, every page
// FILE: frontend/src/components/GlobalAssistant/GlobalAssistantButton.jsx
// BATCH 28 / v10 Global Assistant (new) - The floating action button that
// lives on EVERY page (mounted in App.jsx outside the router). Hidden while
// a live championship is in progress (fairness). Opens the panel.

import React from "react";
import { Sparkles, X } from "lucide-react";
import useTutorStore from "../../store/tutorStore";

export default function GlobalAssistantButton() {
  const { open, locked, toggle } = useTutorStore();
  if (locked) return null; // disabled during a live exam

  return (
    <button
      onClick={toggle}
      aria-label={open ? "Close assistant" : "Open assistant"}
      className="fixed bottom-5 right-5 z-40 h-14 w-14 rounded-full shadow-xl flex items-center justify-center transition hover:scale-105 focus-visible:ring-2 focus-visible:ring-cyan-400 outline-none"
      style={{
        background:
          "radial-gradient(120% 120% at 30% 20%, #22d3ee 0%, #0e7490 60%, #0b3b47 100%)",
      }}
    >
      {open ? (
        <X size={22} className="text-gray-950" />
      ) : (
        <Sparkles size={22} className="text-gray-950" />
      )}
    </button>
  );
}