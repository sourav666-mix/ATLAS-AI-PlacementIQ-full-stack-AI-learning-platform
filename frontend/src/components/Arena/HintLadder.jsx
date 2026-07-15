// HintLadder.jsx - [NEW] 3 progressive hints
// FILE: frontend/src/components/Arena/HintLadder.jsx
// BATCH 27 / v10 Code Arena + DSA (new) - Progressive hints, revealed one
// rung at a time: nudge -> approach -> pseudocode -> full optimal solution.
// The rungs come pre-seeded on the problem (hints_json + optimal_solution),
// so opening a hint is a bank read — NO AI call. Making the student climb
// deliberately (each rung unlocks the next) protects the learning.

import React, { useState } from "react";
import { Lightbulb, ChevronDown } from "lucide-react";

const RUNG_LABELS = ["Nudge", "Approach", "Pseudocode"];

export default function HintLadder({ hints = [], optimal, complexity }) {
  const [revealed, setRevealed] = useState(0); // how many rungs are open
  const [showOptimal, setShowOptimal] = useState(false);

  const rungs = (hints || []).slice(0, 3);
  const hasMore = revealed < rungs.length;

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900 p-5 space-y-3">
      <p className="flex items-center gap-2 text-[11px] uppercase tracking-[0.14em] text-gray-500">
        <Lightbulb size={14} className="text-amber-400" /> Stuck? Climb the hint ladder
      </p>

      {rungs.slice(0, revealed).map((hint, i) => (
        <div key={i} className="rounded-lg bg-gray-950 border border-gray-800 p-3">
          <p className="text-[11px] font-semibold text-amber-400 mb-1">
            {RUNG_LABELS[i] || `Hint ${i + 1}`}
          </p>
          <p className="text-sm text-gray-300 whitespace-pre-wrap">
            {typeof hint === "string" ? hint : hint.text || JSON.stringify(hint)}
          </p>
        </div>
      ))}

      {hasMore && (
        <button
          onClick={() => setRevealed((r) => r + 1)}
          className="w-full flex items-center justify-center gap-1.5 rounded-lg border border-gray-800 py-2 text-xs text-gray-400 hover:text-gray-200 hover:border-gray-600 transition"
        >
          <ChevronDown size={14} />
          Reveal {RUNG_LABELS[revealed] ? RUNG_LABELS[revealed].toLowerCase() : "next hint"}
        </button>
      )}

      {!hasMore && optimal && !showOptimal && (
        <button
          onClick={() => setShowOptimal(true)}
          className="w-full rounded-lg border border-amber-900/60 bg-amber-950/20 py-2 text-xs text-amber-300 hover:bg-amber-950/40 transition"
        >
          I've tried — show the optimal solution
        </button>
      )}

      {showOptimal && optimal && (
        <div className="rounded-lg bg-gray-950 border border-gray-800 p-3 space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-semibold text-emerald-400">
              Optimal solution
            </p>
            {complexity && (
              <span className="text-[11px] text-gray-500 font-mono">{complexity}</span>
            )}
          </div>
          <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono overflow-x-auto">
            {optimal}
          </pre>
        </div>
      )}
    </div>
  );
}