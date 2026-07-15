// FILE: frontend/src/pages/RoadmapDashboard.jsx   [v12 — Live Lab tab wired]
// Roadmap + Live Lab as tabs on the same page. The lab is pre-scoped to this
// domain/topic, so the student never re-selects anything.
import React, { useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import RoadmapView from "../components/SkillPath/RoadmapDashboard";
import LabWorkspace from "../components/LiveLab/LabWorkspace";

export default function RoadmapDashboardPage() {
  const { domainId } = useParams();
  const [params] = useSearchParams();
  const planMonths = Number(params.get("plan")) || undefined;
  const [tab, setTab] = useState("roadmap");

  return (
    <div className="p-8">
      {/* Tab switcher */}
      <div className="flex gap-1 rounded-xl bg-gray-900 p-1 border border-gray-800 w-fit mb-6">
        {[
          { id: "roadmap", label: "Roadmap" },
          { id: "livelab", label: "Live Lab" },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              tab === t.id
                ? "bg-violet-600 text-white"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "roadmap" ? (
        <RoadmapView domainId={domainId} planMonths={planMonths} />
      ) : (
        <LabWorkspace domainId={domainId} />
      )}
    </div>
  );
}