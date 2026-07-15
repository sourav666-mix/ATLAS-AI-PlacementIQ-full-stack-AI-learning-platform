/**
 * Dependency-free SVG radar. Overlays the student's 9 pillars against a
 * selected company's requirements. No chart library — pure trig, VizMount-style.
 */
import React, { useState } from "react";

const PILLARS = [
  "programming", "dsa", "database_sql", "core_domain", "projects",
  "deployment", "aptitude", "communication", "resume_ats",
];
const SHORT = {
  programming: "Prog", dsa: "DSA", database_sql: "SQL", core_domain: "Domain",
  projects: "Proj", deployment: "Deploy", aptitude: "Apti",
  communication: "Comm", resume_ats: "Resume",
};

function polygon(values, radius, cx, cy) {
  const n = PILLARS.length;
  return PILLARS.map((p, i) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    const r = (Math.max(0, Math.min(100, values[p] || 0)) / 100) * radius;
    return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
  }).join(" ");
}

export default function GapRadar({ pillars, targets }) {
  const size = 360;
  const cx = size / 2;
  const cy = size / 2;
  const radius = 130;
  const [activeSlug, setActiveSlug] = useState(targets?.[0]?.company_slug || null);

  const active = targets?.find((t) => t.company_slug === activeSlug) || targets?.[0];
  const need = {};
  (active?.pillar_gaps || []).forEach((g) => (need[g.pillar] = g.need));

  const rings = [0.25, 0.5, 0.75, 1];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-white">Skill Gap Radar</h3>
        <div className="flex flex-wrap gap-1">
          {(targets || []).map((t) => (
            <button
              key={t.company_slug}
              type="button"
              onClick={() => setActiveSlug(t.company_slug)}
              className={`rounded px-2 py-1 text-[11px] font-medium transition ${
                activeSlug === t.company_slug
                  ? "bg-rose-500 text-white"
                  : "bg-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              {t.company_name}
            </button>
          ))}
        </div>
      </div>

      <svg viewBox={`0 0 ${size} ${size}`} className="mx-auto block w-full max-w-sm">
        {rings.map((r, i) => (
          <polygon
            key={i}
            points={polygon(
              Object.fromEntries(PILLARS.map((p) => [p, r * 100])),
              radius, cx, cy
            )}
            fill="none"
            stroke="#1e293b"
            strokeWidth="1"
          />
        ))}
        {PILLARS.map((p, i) => {
          const angle = (Math.PI * 2 * i) / PILLARS.length - Math.PI / 2;
          const x = cx + radius * Math.cos(angle);
          const y = cy + radius * Math.sin(angle);
          const lx = cx + (radius + 22) * Math.cos(angle);
          const ly = cy + (radius + 22) * Math.sin(angle);
          return (
            <g key={p}>
              <line x1={cx} y1={cy} x2={x} y2={y} stroke="#1e293b" strokeWidth="1" />
              <text
                x={lx} y={ly}
                textAnchor="middle" dominantBaseline="middle"
                className="fill-slate-400" fontSize="10"
              >
                {SHORT[p]}
              </text>
            </g>
          );
        })}

        {/* company requirement outline */}
        {active && (
          <polygon
            points={polygon(need, radius, cx, cy)}
            fill="rgba(244,63,94,0.10)"
            stroke="#f43f5e"
            strokeWidth="1.5"
            strokeDasharray="4 3"
          />
        )}
        {/* student */}
        <polygon
          points={polygon(pillars, radius, cx, cy)}
          fill="rgba(16,185,129,0.20)"
          stroke="#10b981"
          strokeWidth="2"
        />
      </svg>

      <div className="mt-3 flex items-center justify-center gap-4 text-[11px]">
        <span className="flex items-center gap-1.5 text-slate-400">
          <span className="h-2 w-4 rounded bg-emerald-500" /> You
        </span>
        <span className="flex items-center gap-1.5 text-slate-400">
          <span className="h-2 w-4 rounded border border-dashed border-rose-500" />
          {active?.company_name || "Target"} needs
        </span>
      </div>
    </div>
  );
}