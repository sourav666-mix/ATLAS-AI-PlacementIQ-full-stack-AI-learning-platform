// RevealCard.jsx - [NEW] why/how/example/mistakes (DB read)
// FILE: frontend/src/components/SkillPath/RevealCard.jsx
// BATCH 26 / v10 SkillPath (new) - The reveal: model answer + why + how +
// example + common mistakes, straight from the question bank (pure DB read,
// NO AI). Rendered only AFTER a scored attempt — attempt-first is the rule.

import React from "react";
import { BookOpenCheck } from "lucide-react";

const FIELDS = [
  ["model_answer", "Model answer"],
  ["answer", "Model answer"],
  ["why", "Why"],
  ["why_explanation", "Why"],
  ["how", "How"],
  ["how_explanation", "How"],
  ["example", "Example"],
  ["common_mistakes", "Common mistakes"],
];

export default function RevealCard({ reveal }) {
  if (!reveal) return null;
  const seen = new Set();
  const blocks = FIELDS.filter(([key, label]) => {
    if (!reveal[key] || seen.has(label)) return false;
    seen.add(label);
    return true;
  });

  return (
    <div className="rounded-2xl border border-emerald-900/70 bg-emerald-950/20 p-5 space-y-4">
      <p className="flex items-center gap-2 text-[11px] uppercase tracking-[0.14em] text-emerald-400">
        <BookOpenCheck size={14} /> From the answer bank
      </p>
      {blocks.map(([key, label]) => (
        <div key={key}>
          <p className="text-xs font-semibold text-emerald-300 mb-1">{label}</p>
          <p className="text-sm leading-relaxed text-gray-300 whitespace-pre-wrap">
            {reveal[key]}
          </p>
        </div>
      ))}
      {!blocks.length && (
        <p className="text-sm text-gray-400">
          This question's reveal content isn't seeded yet.
        </p>
      )}
    </div>
  );
}