// FILE: frontend/src/components/Dashboard/ProfileBar.jsx
// BATCH 25 / v10 Dashboard (new) - THE signature element. The Profile
// Improvement Bar is drawn as a weighted spectrum: six segments whose WIDTHS
// are the real Section-5 formula weights (25/20/20/15/10/10) and whose FILL
// is that component's score. The structure IS the math — a student can see
// at a glance both how much each area counts and how full it is. The
// weakest-leverage segment gets the "what raises this next" call to action.

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";

const META = {
  skill_mastery:      { label: "Skill mastery",  color: "#22d3ee", to: "/roadmap" },
  assessment_history: { label: "Assessments",    color: "#a78bfa", to: "/assessment" },
  coding_strength:    { label: "Coding",         color: "#34d399", to: "/arena" },
  interview_readiness:{ label: "Interviews",     color: "#fbbf24", to: "/studio" },
  resume_completeness:{ label: "Resume",         color: "#f472b6", to: "/resume" },
  consistency:        { label: "Consistency",    color: "#38bdf8", to: "/dashboard" },
};

export default function ProfileBar({ score, components, weights, next, order }) {
  const [hover, setHover] = useState(null);
  const navigate = useNavigate();

  // Highest-leverage gap = weight x (100 - score); that's where the CTA points.
  let target = null;
  let bestGap = -1;
  order.forEach((key) => {
    const gap = (weights[key] || 0) * (100 - Number(components[key] ?? 0));
    if (gap > bestGap) { bestGap = gap; target = key; }
  });

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <div className="flex items-end justify-between mb-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">
            Profile improvement bar
          </p>
          <p className="text-4xl font-bold text-gray-50 tabular-nums leading-tight">
            {score}
            <span className="text-lg text-gray-500 font-medium"> / 100</span>
          </p>
        </div>
        {hover && (
          <div className="text-right">
            <p className="text-xs" style={{ color: META[hover].color }}>
              {META[hover].label}
            </p>
            <p className="text-sm text-gray-300 tabular-nums">
              {Math.round(components[hover] ?? 0)}/100 · counts {weights[hover]}%
            </p>
          </div>
        )}
      </div>

      {/* The spectrum: segment width = weight, fill = score */}
      <div className="flex w-full h-4 rounded-full overflow-hidden gap-[3px]">
        {order.map((key) => {
          const meta = META[key];
          const value = Math.max(0, Math.min(100, Number(components[key] ?? 0)));
          const isTarget = key === target;
          return (
            <button
              key={key}
              onMouseEnter={() => setHover(key)}
              onMouseLeave={() => setHover(null)}
              onClick={() => navigate(meta.to)}
              title={`${meta.label}: ${Math.round(value)}/100 (counts ${weights[key]}%)`}
              className="relative h-full bg-gray-800 outline-none focus-visible:ring-2 focus-visible:ring-cyan-400"
              style={{ width: `${weights[key]}%` }}
            >
              <span
                className="absolute inset-y-0 left-0 transition-all duration-700"
                style={{
                  width: `${value}%`,
                  background: meta.color,
                  opacity: hover && hover !== key ? 0.35 : 1,
                }}
              />
              {isTarget && (
                <span className="absolute -top-1.5 left-1/2 -translate-x-1/2 h-1.5 w-1.5 rounded-full bg-white" />
              )}
            </button>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
        {order.map((key) => (
          <span key={key} className="flex items-center gap-1.5 text-[11px] text-gray-500">
            <span
              className="h-2 w-2 rounded-full"
              style={{ background: META[key].color }}
            />
            {META[key].label} {weights[key]}%
          </span>
        ))}
      </div>

      {/* What raises this next */}
      {target && (
        <button
          onClick={() => navigate(META[target].to)}
          className="mt-4 w-full flex items-center justify-between rounded-xl border border-gray-800 bg-gray-950 px-4 py-3 text-left hover:border-gray-600 transition group"
        >
          <div>
            <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">
              Raises this fastest
            </p>
            <p className="text-sm text-gray-200">
              {next || `Work on ${META[target].label.toLowerCase()} — it has the most headroom right now.`}
            </p>
          </div>
          <ArrowRight
            size={16}
            className="text-gray-500 group-hover:text-cyan-400 group-hover:translate-x-0.5 transition"
          />
        </button>
      )}
    </div>
  );
}