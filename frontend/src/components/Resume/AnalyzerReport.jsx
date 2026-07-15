// AnalyzerReport.jsx - [NEW] ATS + match + STAR + top-3 questions
// FILE: frontend/src/components/Resume/AnalyzerReport.jsx
// BATCH 29 / v10 Resume AI (new) - The analysis report: ATS score gauge,
// section-by-section review, Smart Job Matcher (matched/missing/transferable),
// STAR rewrites, missing-content radar (each linking into SkillPath), and the
// top-3 predicted interview questions with a jump into Interview Studio.
// Deep links honour the product spec's one-click flows.

import React from "react";
import { useNavigate } from "react-router-dom";
import { Mic, ArrowUpRight } from "lucide-react";
import { ProgressRing, Badge, Button } from "../Common";

function toList(v) {
  if (!v) return [];
  return Array.isArray(v) ? v : [v];
}

export default function AnalyzerReport({ report, onRebuild, rebuilding }) {
  const navigate = useNavigate();
  if (!report) return null;

  const ats = Math.round(Number(report.ats_score ?? report.ats ?? 0));
  const match = report.match_score != null
    ? Math.round(Number(report.match_score))
    : null;
  const sections = report.sections || report.section_review || [];
  const matched = toList(report.matched_skills);
  const missing = toList(report.missing_skills);
  const transferable = toList(report.transferable_skills);
  const star = toList(report.star_rewrites || report.star_bullets);
  const gaps = toList(report.missing_content || report.missing_radar);
  const questions = toList(report.top_questions || report.predicted_questions);

  const atsColor = ats >= 75 ? "#34d399" : ats >= 50 ? "#fbbf24" : "#f87171";

  return (
    <div className="space-y-4">
      {/* Scores */}
      <div className="rise grid sm:grid-cols-2 gap-4" style={{ "--d": "0ms" }}>
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 flex items-center gap-5">
          <ProgressRing
            value={ats} max={100} size={104} stroke={9} color={atsColor}
            label={
              <div>
                <p className="text-2xl font-bold text-gray-50 tabular-nums leading-none">{ats}</p>
                <p className="text-[10px] text-gray-500 mt-0.5">ATS</p>
              </div>
            }
          />
          <div>
            <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">ATS readiness</p>
            <p className="text-sm text-gray-300 mt-1">
              {ats >= 75 ? "Strong — minor polish only." : ats >= 50 ? "Fixable gaps below." : "Needs real work — start at the top of the fix list."}
            </p>
          </div>
        </div>
        {match != null && (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 flex items-center gap-5">
            <ProgressRing
              value={match} max={100} size={104} stroke={9} color="#22d3ee"
              label={
                <div>
                  <p className="text-2xl font-bold text-gray-50 tabular-nums leading-none">{match}%</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">JD match</p>
                </div>
              }
            />
            <div>
              <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Semantic match</p>
              <p className="text-sm text-gray-300 mt-1">
                {matched.length} matched · {missing.length} missing skills
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Section review */}
      {sections.length > 0 && (
        <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3" style={{ "--d": "80ms" }}>
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Section review</p>
          {sections.map((s, i) => (
            <div key={i} className="rounded-xl bg-gray-950 border border-gray-800 p-3">
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-semibold text-gray-200 capitalize">
                  {s.name || s.section}
                </p>
                {s.score != null && (
                  <span className="text-xs text-gray-500 tabular-nums">{Math.round(s.score)}/100</span>
                )}
              </div>
              {s.strong && <p className="text-xs text-emerald-400">✓ {s.strong}</p>}
              {s.weak && <p className="text-xs text-amber-400">△ {s.weak}</p>}
              {s.missing && <p className="text-xs text-red-400">✗ {s.missing}</p>}
              {s.feedback && <p className="text-xs text-gray-400 mt-1">{s.feedback}</p>}
            </div>
          ))}
        </div>
      )}

      {/* Skills */}
      {(matched.length || missing.length || transferable.length) > 0 && (
        <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3" style={{ "--d": "140ms" }}>
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Skill match</p>
          {matched.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {matched.map((s, i) => <Badge key={i} tone="green">{s}</Badge>)}
            </div>
          )}
          {missing.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-1.5">Missing for this JD</p>
              <div className="flex flex-wrap gap-1.5">
                {missing.map((s, i) => <Badge key={i} tone="red">{s}</Badge>)}
              </div>
            </div>
          )}
          {transferable.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-1.5">You have these — phrase them better</p>
              <div className="flex flex-wrap gap-1.5">
                {transferable.map((s, i) => <Badge key={i} tone="amber">{s}</Badge>)}
              </div>
            </div>
          )}
        </div>
      )}

      {/* STAR rewrites */}
      {star.length > 0 && (
        <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3" style={{ "--d": "200ms" }}>
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">STAR rewrites</p>
          {star.map((item, i) => (
            <div key={i} className="rounded-xl bg-gray-950 border border-gray-800 p-3 space-y-1.5">
              {item.original && <p className="text-xs text-gray-500 line-through">{item.original}</p>}
              <p className="text-sm text-emerald-300">{item.rewrite || item.improved || item}</p>
            </div>
          ))}
        </div>
      )}

      {/* Missing-content radar with SkillPath links */}
      {gaps.length > 0 && (
        <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-2" style={{ "--d": "260ms" }}>
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Close these gaps in ATLAS</p>
          {gaps.map((g, i) => (
            <button
              key={i}
              onClick={() => g.topic_id && navigate(`/learn/${g.topic_id}`)}
              className="w-full flex items-center justify-between rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-left hover:border-gray-600 transition group"
            >
              <span className="text-sm text-gray-300">
                {g.item || g.label || g} {g.suggestion && <span className="text-gray-500">— {g.suggestion}</span>}
              </span>
              {g.topic_id && <ArrowUpRight size={14} className="text-gray-600 group-hover:text-cyan-400" />}
            </button>
          ))}
        </div>
      )}

      {/* Top-3 predicted questions */}
      {questions.length > 0 && (
        <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3" style={{ "--d": "320ms" }}>
          <div className="flex items-center justify-between">
            <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Predicted interview questions</p>
            <Button size="sm" variant="ghost" onClick={() => navigate("/studio")}>
              <Mic size={13} className="inline mr-1" /> Practice these
            </Button>
          </div>
          <ol className="space-y-2">
            {questions.map((q, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-300">
                <span className="text-cyan-400 font-semibold">{i + 1}.</span>
                {typeof q === "string" ? q : q.question}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Rebuild CTA */}
      <div className="rise" style={{ "--d": "380ms" }}>
        <Button size="lg" onClick={onRebuild} disabled={rebuilding}>
          {rebuilding ? "Building improved PDF…" : "Rebuild as an ATS-optimized PDF"}
        </Button>
      </div>
    </div>
  );
}