// SubtopicChecklist.jsx - [NEW] subtopic checklist at top of topic
// FILE: frontend/src/components/SkillPath/SubtopicChecklist.jsx
// BATCH 26 / v10 SkillPath (new) - The subtopic rail inside a topic:
// pick a subtopic to study; ticks show mastery earned by real attempts.

import React from "react";
import { CheckCircle2 } from "lucide-react";

export default function SubtopicChecklist({ subtopics, activeId, onSelect }) {
  return (
    <div className="space-y-1.5">
      {subtopics.map((sub, index) => {
        const active = sub.id === activeId;
        const done = sub.status === "completed" || sub.mastery >= 80;
        return (
          <button
            key={sub.id}
            onClick={() => onSelect(sub)}
            className={`w-full flex items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
              active
                ? "bg-cyan-950/50 text-cyan-200 border border-cyan-900"
                : "text-gray-400 hover:bg-gray-900 border border-transparent"
            }`}
          >
            {done ? (
              <CheckCircle2 size={15} className="text-emerald-400 shrink-0" />
            ) : (
              <span className="h-4 w-4 rounded-full border border-gray-700 text-[9px] text-gray-600 flex items-center justify-center shrink-0">
                {index + 1}
              </span>
            )}
            <span className="flex-1 truncate">{sub.name}</span>
            {sub.mastery > 0 && !done && (
              <span className="text-[10px] text-gray-600 tabular-nums">
                {sub.mastery}%
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}