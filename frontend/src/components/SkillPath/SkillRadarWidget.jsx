// SkillRadarWidget.jsx - dashboard radar widget
// FILE: frontend/src/components/SkillPath/SkillRadarWidget.jsx
// BATCH 25 / v10 Dashboard (new) - The radar card. Empty state is an
// invitation to act, not a shrug: it routes to the roadmap.

import React from "react";
import { useNavigate } from "react-router-dom";
import RadarChart from "../Charts/RadarChart";
import { Button } from "../Common";

export default function SkillRadarWidget({ radar }) {
  const navigate = useNavigate();
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 h-full">
      <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500 mb-1">
        Skill radar
      </p>
      {radar.length >= 3 ? (
        <RadarChart data={radar} />
      ) : (
        <div className="h-[260px] flex flex-col items-center justify-center text-center gap-3">
          <p className="text-sm text-gray-400 max-w-[220px]">
            Your radar draws itself as you practice. Score your first
            questions to see it take shape.
          </p>
          <Button size="sm" onClick={() => navigate("/roadmap")}>
            Start practicing
          </Button>
        </div>
      )}
    </div>
  );
}