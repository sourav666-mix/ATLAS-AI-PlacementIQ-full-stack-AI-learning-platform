/**
 * 12-week closing plan. Every action links to an internal ATLAS route only —
 * the backend sanitizer guarantees no external link can reach this component.
 */
import React from "react";
import { useNavigate } from "react-router-dom";

const SOURCE_BADGE = {
  ai: { text: "AI plan", cls: "bg-violet-600" },
  cache: { text: "Saved plan", cls: "bg-slate-600" },
  fallback: { text: "Rule-based plan", cls: "bg-amber-600" },
};

export default function PlanTimeline({ report }) {
  const navigate = useNavigate();
  if (!report) return null;

  const badge = SOURCE_BADGE[report.source] || SOURCE_BADGE.cache;
  const plan = report.plan || [];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-white">Your 12-Week Plan</h3>
          <p className="text-xs text-slate-500">
            Everything below is built inside ATLAS. You never need another platform.
          </p>
        </div>
        <span className={`rounded-full px-2 py-1 text-[10px] font-medium text-white ${badge.cls}`}>
          {badge.text}
        </span>
      </div>

      {report.headline && (
        <p className="mb-4 rounded-lg bg-slate-900 px-3 py-2 text-sm text-slate-300">
          {report.headline}
        </p>
      )}

      {(report.strengths?.length || report.critical_gaps?.length) && (
        <div className="mb-5 grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg border border-emerald-900/50 bg-emerald-950/20 p-3">
            <div className="mb-1 text-xs font-semibold text-emerald-400">Strengths</div>
            <ul className="space-y-1 text-xs text-slate-300">
              {(report.strengths || []).map((s, i) => (
                <li key={i}>• {s}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-lg border border-rose-900/50 bg-rose-950/20 p-3">
            <div className="mb-1 text-xs font-semibold text-rose-400">Close these first</div>
            <ul className="space-y-1 text-xs text-slate-300">
              {(report.critical_gaps || []).map((s, i) => (
                <li key={i}>• {s}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <div className="relative space-y-3 border-l border-slate-800 pl-5">
        {plan.map((wk) => (
          <div key={wk.week} className="relative">
            <span className="absolute -left-[27px] top-1 flex h-5 w-5 items-center justify-center rounded-full bg-emerald-600 text-[10px] font-bold text-slate-900">
              {wk.week}
            </span>
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
              <div className="mb-2 text-sm font-medium text-white">
                Week {wk.week} — {wk.theme}
              </div>
              <div className="space-y-2">
                {(wk.actions || []).map((a) => (
                  <button
                    key={a.action_id}
                    type="button"
                    onClick={() => navigate(a.route)}
                    className="group flex w-full items-center justify-between rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-left transition hover:border-emerald-500"
                  >
                    <div>
                      <div className="text-xs font-medium text-white">{a.label}</div>
                      <div className="text-[11px] text-slate-500">{a.why}</div>
                    </div>
                    <div className="flex items-center gap-2 pl-3">
                      <span className="text-[10px] text-slate-500">~{a.est_hours}h</span>
                      <span className="text-emerald-500 group-hover:translate-x-0.5">→</span>
                    </div>
                  </button>
                ))}
              </div>
              {wk.checkpoint && (
                <p className="mt-2 text-[11px] text-slate-500">✓ {wk.checkpoint}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}