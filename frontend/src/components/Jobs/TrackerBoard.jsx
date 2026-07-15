// TrackerBoard.jsx - [NEW] application pipeline kanban
// FILE: frontend/src/components/Jobs/TrackerBoard.jsx
// BATCH 29 / v10 Jobs Board (new) - The application pipeline as a kanban:
// saved -> applied -> test -> interview -> offer (+ rejected). Each saved job
// sits in its current stage column; clicking a stage on the card advances it.
// Read-only board view here; the advance action lives on JobCard.

import React from "react";

const COLUMNS = [
  { key: "saved", label: "Saved", tone: "#6b7280" },
  { key: "applied", label: "Applied", tone: "#38bdf8" },
  { key: "test", label: "Test", tone: "#a78bfa" },
  { key: "interview", label: "Interview", tone: "#fbbf24" },
  { key: "offer", label: "Offer", tone: "#34d399" },
  { key: "rejected", label: "Rejected", tone: "#f87171" },
];

export default function TrackerBoard({ jobs = [], onOpen }) {
  const byStage = {};
  COLUMNS.forEach((c) => (byStage[c.key] = []));
  jobs.forEach((j) => {
    const stage = j.stage || "saved";
    (byStage[stage] || byStage.saved).push(j);
  });

  const active = COLUMNS.filter((c) => byStage[c.key].length > 0);
  if (!active.length) {
    return (
      <p className="text-sm text-gray-500">
        Save a posting to start tracking it through the pipeline.
      </p>
    );
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {COLUMNS.map((col) => (
        <div key={col.key} className="min-w-[13rem] flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="h-2 w-2 rounded-full" style={{ background: col.tone }} />
            <p className="text-xs font-semibold text-gray-400">{col.label}</p>
            <span className="text-[11px] text-gray-600 tabular-nums">
              {byStage[col.key].length}
            </span>
          </div>
          <div className="space-y-2">
            {byStage[col.key].map((job) => (
              <button
                key={job.id}
                onClick={() => onOpen && onOpen(job)}
                className="w-full text-left rounded-xl border border-gray-800 bg-gray-950 p-3 hover:border-gray-600 transition"
              >
                <p className="text-sm text-gray-200 truncate">{job.role || job.title}</p>
                <p className="text-xs text-gray-500 truncate">{job.company}</p>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}