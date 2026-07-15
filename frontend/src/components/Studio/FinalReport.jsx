// FinalReport.jsx - [NEW] strengths/weaknesses/platform plan
// FILE: frontend/src/components/Studio/FinalReport.jsx
// BATCH 31 / v10 Interview Studio (new) - The final report: overall + per-
// question scores, strengths, weaknesses, communication notes, presence
// summary, and the personalized improvement plan whose links point at REAL
// platform features (SkillPath topic, DSA Gym, Resume trainer). This is the
// "closes its own loop" moment — every weakness maps to a place to fix it.

import React from "react";
import { useNavigate } from "react-router-dom";
import { Award, ArrowUpRight, Eye } from "lucide-react";
import { ProgressRing, Badge, Button } from "../Common";

// Map a plan item's target to an in-app route.
function routeFor(item) {
  const t = (item.target || item.feature || "").toLowerCase();
  if (item.topic_id) return `/learn/${item.topic_id}`;
  if (t.includes("dsa")) return "/dsa";
  if (t.includes("arena") || t.includes("cod")) return "/arena";
  if (t.includes("resume")) return "/resume";
  if (t.includes("skillpath") || t.includes("roadmap") || t.includes("topic")) return "/roadmap";
  if (t.includes("assess") || t.includes("aptitude") || t.includes("mock")) return "/assessment";
  return null;
}

function toList(v) {
  if (!v) return [];
  return Array.isArray(v) ? v : [v];
}

export default function FinalReport({ report, turns, presence, onDone }) {
  const navigate = useNavigate();
  const r = report || {};
  const overall = Math.round(Number(r.overall_score ?? r.score ?? 0));
  const strengths = toList(r.strengths);
  const weaknesses = toList(r.weaknesses);
  const comm = r.communication || r.communication_notes;
  const plan = toList(r.improvement_plan || r.plan);

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-6 flex items-center gap-6" style={{ "--d": "0ms" }}>
        <ProgressRing
          value={overall} max={10} size={120} stroke={10}
          color={overall >= 7 ? "#34d399" : overall >= 4 ? "#fbbf24" : "#f87171"}
          label={
            <div>
              <p className="text-2xl font-bold text-gray-50 tabular-nums leading-none">{overall}</p>
              <p className="text-[10px] text-gray-500 mt-0.5">/ 10</p>
            </div>
          }
        />
        <div className="space-y-1.5">
          <p className="flex items-center gap-2 text-lg font-bold text-gray-100">
            <Award size={18} className="text-amber-400" /> Interview complete
          </p>
          {presence?.presence_pct != null && (
            <p className="text-sm text-gray-400 flex items-center gap-1.5">
              <Eye size={14} /> {presence.presence_pct}% on-camera presence
              {presence.look_aways ? ` · ${presence.look_aways} long look-aways` : ""}
            </p>
          )}
          {r.points_awarded != null && <Badge tone="green">+{r.points_awarded} points</Badge>}
        </div>
      </div>

      {(strengths.length || weaknesses.length) > 0 && (
        <div className="rise grid sm:grid-cols-2 gap-4" style={{ "--d": "80ms" }}>
          {strengths.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
              <p className="text-xs font-semibold text-emerald-400 mb-2">Strengths</p>
              <ul className="space-y-1.5 text-sm text-gray-300">
                {strengths.map((s, i) => <li key={i}>✓ {typeof s === "string" ? s : s.text}</li>)}
              </ul>
            </div>
          )}
          {weaknesses.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
              <p className="text-xs font-semibold text-amber-400 mb-2">To work on</p>
              <ul className="space-y-1.5 text-sm text-gray-300">
                {weaknesses.map((s, i) => <li key={i}>△ {typeof s === "string" ? s : s.text}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {comm && (
        <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5" style={{ "--d": "140ms" }}>
          <p className="text-xs font-semibold text-cyan-400 mb-1">Communication</p>
          <p className="text-sm text-gray-300 leading-relaxed">
            {typeof comm === "string" ? comm : JSON.stringify(comm)}
          </p>
        </div>
      )}

      {/* The loop-closing improvement plan */}
      {plan.length > 0 && (
        <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-2" style={{ "--d": "200ms" }}>
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Your improvement plan</p>
          {plan.map((item, i) => {
            const route = routeFor(item);
            return (
              <button
                key={i}
                onClick={() => route && navigate(route)}
                disabled={!route}
                className="w-full flex items-center justify-between rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-left hover:border-gray-600 transition group disabled:opacity-70"
              >
                <span className="text-sm text-gray-300">
                  {item.label || item.text || item.issue}
                  {item.action && <span className="text-cyan-400"> → {item.action}</span>}
                </span>
                {route && <ArrowUpRight size={14} className="text-gray-600 group-hover:text-cyan-400" />}
              </button>
            );
          })}
        </div>
      )}

      {/* Per-question review */}
      {turns?.length > 0 && (
        <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3" style={{ "--d": "260ms" }}>
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Question-by-question</p>
          {turns.map((t, i) => (
            <div key={i} className="rounded-xl bg-gray-950 border border-gray-800 p-3">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm text-gray-200 flex-1">{i + 1}. {t.question}</p>
                {t.score != null && (
                  <span className={`text-xs font-bold tabular-nums ${t.score >= 7 ? "text-emerald-400" : t.score >= 4 ? "text-amber-400" : "text-red-400"}`}>
                    {t.score}/10
                  </span>
                )}
              </div>
              {t.feedback && <p className="text-xs text-gray-400 mt-1.5">{t.feedback}</p>}
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <Button onClick={onDone}>New interview</Button>
        <Button variant="outline" onClick={() => navigate("/dashboard")}>Back to dashboard</Button>
      </div>
    </div>
  );
}