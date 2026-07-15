/**
 * The headline result: profile score + a "% to close" ring per company.
 * This is the exact surface from the brief: "Amazon 60%, TCS 35%, Deloitte 45%".
 */
import React from "react";

function Ring({ pct, color, label, sub }) {
  const r = 34;
  const c = 2 * Math.PI * r;
  const offset = c - (pct / 100) * c;
  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 90 90" className="h-24 w-24">
        <circle cx="45" cy="45" r={r} fill="none" stroke="#1e293b" strokeWidth="8" />
        <circle
          cx="45" cy="45" r={r} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round"
          transform="rotate(-90 45 45)"
        />
        <text
          x="45" y="42" textAnchor="middle" className="fill-white"
          fontSize="18" fontWeight="700"
        >
          {pct}%
        </text>
        <text x="45" y="58" textAnchor="middle" className="fill-slate-500" fontSize="8">
          to close
        </text>
      </svg>
      <div className="mt-1 text-center">
        <div className="text-sm font-semibold text-white">{label}</div>
        <div className="text-[11px] text-slate-500">{sub}</div>
      </div>
    </div>
  );
}

const gapColor = (gap) =>
  gap <= 30 ? "#10b981" : gap <= 50 ? "#f59e0b" : "#f43f5e";

export default function GapScoreCards({ result }) {
  if (!result) return null;
  const { profile_score, profile_grade, targets = [] } = result;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white">Your Readiness</h3>
          <p className="text-xs text-slate-500">Computed with pure math — no AI, no guessing.</p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-emerald-400">{profile_score}</div>
          <div className="text-[11px] uppercase tracking-wide text-slate-500">
            {profile_grade}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {targets.map((t) => (
          <div
            key={t.company_slug}
            className="flex flex-col items-center rounded-lg border border-slate-800 bg-slate-900/60 p-3"
          >
            <Ring
              pct={t.gap_pct}
              color={gapColor(t.gap_pct)}
              label={t.company_name}
              sub={`#${t.priority} · bar ${t.hiring_bar}`}
            />
            <p className="mt-2 text-center text-[11px] text-slate-400">{t.verdict}</p>
            {t.pillar_gaps?.[0] && (
              <p className="mt-1 text-center text-[10px] text-slate-500">
                biggest lever: {t.pillar_gaps[0].label}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}