// FILE: frontend/src/components/SkillPath/ConceptCard.jsx
// BATCH 26 / v10 SkillPath (new) - The pre-seeded concept card (Type A —
// served from topic_content, zero AI). Sections render only when present.

import React from "react";

const SECTIONS = [
  ["theory", "The idea"],
  ["explanation", "The idea"],
  ["why", "Why it matters"],
  ["how", "How it works"],
  ["example", "Worked example"],
  ["analogy", "Think of it like"],
  ["common_mistakes", "Common mistakes"],
  ["interview_angle", "How interviews ask this"],
];

export default function ConceptCard({ concept }) {
  if (!concept) return null;
  const seen = new Set();
  const blocks = SECTIONS.filter(([key, label]) => {
    if (!concept[key] || seen.has(label)) return false;
    seen.add(label);
    return true;
  });
  if (!blocks.length && !concept.content) return null;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
      <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">
        Concept
      </p>
      {concept.content && (
        <p className="text-sm leading-relaxed text-gray-300 whitespace-pre-wrap">
          {concept.content}
        </p>
      )}
      {blocks.map(([key, label]) => (
        <div key={key}>
          <p className="text-xs font-semibold text-cyan-400 mb-1">{label}</p>
          <p className="text-sm leading-relaxed text-gray-300 whitespace-pre-wrap">
            {concept[key]}
          </p>
        </div>
      ))}
    </div>
  );
}