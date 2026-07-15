// FILE: frontend/src/components/SkillPath/SubtopicPills.jsx
// v12 — mastery pills: locked / in_progress / mastered, each with its 0..25 counter.
import React from "react";

const STYLE = {
  locked: "border-gray-700 text-gray-500 bg-gray-950",
  in_progress: "border-violet-500 text-violet-200 bg-violet-500/10",
  mastered: "border-emerald-500 text-emerald-200 bg-emerald-500/10",
};

export default function SubtopicPills({ pills = [], onSelect }) {
  if (!pills.length) {
    return <p className="text-sm text-gray-500">No subtopics seeded yet.</p>;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {pills.map((p) => (
        <button
          key={p.subtopic_id}
          onClick={() => onSelect && onSelect(p.subtopic_id)}
          className={`rounded-full border px-3 py-1.5 text-sm transition-colors hover:brightness-125 ${
            STYLE[p.status] || STYLE.locked
          }`}
          title={`Mastery ${p.mastery_score ?? 0}%`}
        >
          <span className="font-medium">{p.name}</span>
          <span className="ml-2 opacity-70">{p.questions_completed ?? 0}/25</span>
          {p.status === "mastered" && <span className="ml-1">✓</span>}
        </button>
      ))}
    </div>
  );
}