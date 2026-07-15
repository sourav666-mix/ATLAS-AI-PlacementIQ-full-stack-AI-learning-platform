// MatchBadge.jsx - [NEW] personal match score badge
// FILE: frontend/src/components/Jobs/MatchBadge.jsx
// BATCH 29 / v10 Jobs Board (new) - The personal 0-100 match score (pure NLP,
// no LLM). Color codes by band; below 60 shows the "close the gap" cue.

import React from "react";

export default function MatchBadge({ score, size = "md" }) {
  const s = Math.round(Number(score ?? 0));
  const color = s >= 80 ? "#34d399" : s >= 60 ? "#22d3ee" : "#fbbf24";
  const dim = size === "sm" ? 44 : 56;
  const stroke = size === "sm" ? 4 : 5;
  const r = (dim - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - s / 100);
  return (
    <div className="relative inline-flex items-center justify-center shrink-0" style={{ width: dim, height: dim }}>
      <svg width={dim} height={dim} className="-rotate-90">
        <circle cx={dim / 2} cy={dim / 2} r={r} stroke="#1f2937" strokeWidth={stroke} fill="none" />
        <circle cx={dim / 2} cy={dim / 2} r={r} stroke={color} strokeWidth={stroke} fill="none"
          strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={offset} />
      </svg>
      <span className="absolute text-xs font-bold tabular-nums" style={{ color }}>{s}</span>
    </div>
  );
}