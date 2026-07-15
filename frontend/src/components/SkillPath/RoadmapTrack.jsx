// RoadmapTrack.jsx - phase timeline (grey/blue/green)
// FILE: frontend/src/components/SkillPath/RoadmapTrack.jsx
// BATCH 26 / v10 SkillPath (new) - The roadmap as a vertical rail: phases
// are stations, topics hang off each station with a mastery meter. The rail
// itself fills with overall progress — the structure shows the journey.
// Normalizes whatever shape /roadmap/my-roadmap returns (phases[] with
// topics[], or a flat topic list with phase names).

import React, { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, ChevronRight, Lock } from "lucide-react";

function normalize(raw) {
  const data = raw || {};
  let phases = data.phases || data.roadmap || null;
  // Backend RoadmapOut sends a flat `items` list with phase_name on each row.
  const flat = Array.isArray(data.topics) ? data.topics
    : Array.isArray(data.items) ? data.items : null;
  if (!phases && flat) {
    const grouped = {};
    flat.forEach((t) => {
      const key = t.phase_name || t.phase || "Your topics";
      (grouped[key] = grouped[key] || []).push(t);
    });
    phases = Object.entries(grouped).map(([name, topics]) => ({ name, topics }));
  }
  if (!phases && Array.isArray(data)) phases = [{ name: "Your topics", topics: data }];
  return (phases || []).map((phase, i) => ({
    id: phase.id || `phase-${i}`,
    name: phase.name || phase.title || `Phase ${i + 1}`,
    topics: (phase.topics || phase.items || []).map((t) => ({
      id: t.id || t.topic_id,
      name: t.name || t.title,
      mastery: Math.round(Number(t.mastery_score ?? t.mastery ?? 0)),
      status: t.status || (Number(t.mastery_score ?? 0) >= 80 ? "completed" : "pending"),
      locked: !!t.locked,
      subtopicsDone: t.subtopics_completed ?? null,
      subtopicsTotal: t.subtopics_total ?? null,
    })),
  }));
}

export default function RoadmapTrack({ roadmap }) {
  const navigate = useNavigate();
  const phases = useMemo(() => normalize(roadmap), [roadmap]);

  if (!phases.length)
    return (
      <p className="text-sm text-gray-500">
        Your roadmap is empty — the backend returned no topics. Check that the
        domain is seeded.
      </p>
    );

  return (
    <div className="space-y-6">
      {phases.map((phase, phaseIndex) => {
        const done = phase.topics.filter((t) => t.status === "completed").length;
        return (
          <div key={phase.id} className="relative pl-8">
            {/* Rail */}
            <span className="absolute left-[9px] top-8 bottom-0 w-px bg-gray-800" />
            <span
              className={`absolute left-0 top-1 h-5 w-5 rounded-full border-2 flex items-center justify-center text-[10px] font-bold ${
                done === phase.topics.length && phase.topics.length
                  ? "border-emerald-500 bg-emerald-950 text-emerald-400"
                  : "border-gray-700 bg-gray-900 text-gray-500"
              }`}
            >
              {phaseIndex + 1}
            </span>

            <div className="flex items-baseline justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-200">{phase.name}</h3>
              <span className="text-[11px] text-gray-600 tabular-nums">
                {done}/{phase.topics.length} topics
              </span>
            </div>

            <div className="space-y-2">
              {phase.topics.map((topic) => (
                <button
                  key={topic.id}
                  disabled={topic.locked}
                  onClick={() =>
                    navigate(`/learn/${topic.id}`, {
                      state: { topicName: topic.name },
                    })
                  }
                  className="w-full group flex items-center gap-3 rounded-xl border border-gray-800 bg-gray-900 px-4 py-3 text-left transition hover:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed outline-none focus-visible:ring-2 focus-visible:ring-cyan-400"
                >
                  {topic.locked ? (
                    <Lock size={16} className="text-gray-600 shrink-0" />
                  ) : topic.status === "completed" ? (
                    <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
                  ) : (
                    <span className="h-4 w-4 rounded-full border border-gray-600 shrink-0" />
                  )}
                  <span className="flex-1 min-w-0">
                    <span className="block text-sm text-gray-200 truncate">
                      {topic.name}
                    </span>
                    <span className="mt-1.5 block h-1 rounded-full bg-gray-800 overflow-hidden">
                      <span
                        className="block h-full rounded-full bg-cyan-500 transition-all duration-700"
                        style={{ width: `${topic.mastery}%` }}
                      />
                    </span>
                  </span>
                  <span className="text-[11px] text-gray-500 tabular-nums shrink-0">
                    {topic.mastery}%
                  </span>
                  <ChevronRight
                    size={15}
                    className="text-gray-600 group-hover:text-cyan-400 shrink-0"
                  />
                </button>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}