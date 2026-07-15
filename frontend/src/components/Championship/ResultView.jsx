// ResultView.jsx - [NEW] rank + breakdown + next steps
// FILE: frontend/src/components/Championship/ResultView.jsx
// BATCH 30 / v10 Championship (new) - Post-exam result: rank, score,
// percentile, attention score, topic breakdown, and "what to practice next"
// links into SkillPath. If the sheet was locked (violation), it says so
// plainly. Detailed AI notes appear only after the admin runs batch analysis
// and publishes — until then this shows the raw score + a "pending" note.

import React from "react";
import { useNavigate } from "react-router-dom";
import { Trophy, Eye, ShieldAlert, ArrowUpRight } from "lucide-react";
import { ProgressRing, Badge, Button } from "../Common";

export default function ResultView({ result, locked, onBackToLobby }) {
  const navigate = useNavigate();
  const r = result || {};
  const published = r.published ?? (r.rank != null || r.percentile != null);
  const score = Math.round(Number(r.score ?? 0));
  const total = Number(r.total ?? 20);
  const pct = total ? Math.round((score / total) * 100) : 0;
  const breakdown = r.topic_breakdown || r.breakdown || [];
  const practice = r.practice_next || r.what_next || [];

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      {locked && (
        <div className="rounded-2xl border border-red-900 bg-red-950/30 p-4 flex items-center gap-3">
          <ShieldAlert size={18} className="text-red-400 shrink-0" />
          <p className="text-sm text-red-300">
            Your exam was locked after you left full-screen. It was submitted as
            it stood at that moment.
          </p>
        </div>
      )}

      <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-6 flex items-center gap-6" style={{ "--d": "0ms" }}>
        <ProgressRing
          value={score} max={total} size={120} stroke={10}
          color={pct >= 70 ? "#34d399" : pct >= 40 ? "#fbbf24" : "#f87171"}
          label={
            <div>
              <p className="text-2xl font-bold text-gray-50 tabular-nums leading-none">{score}</p>
              <p className="text-[10px] text-gray-500 mt-0.5">/ {total}</p>
            </div>
          }
        />
        <div className="space-y-1.5">
          {r.rank != null && (
            <p className="flex items-center gap-2 text-lg font-bold text-gray-100">
              <Trophy size={18} className="text-amber-400" /> Rank #{r.rank}
            </p>
          )}
          {r.percentile != null && (
            <p className="text-sm text-gray-400">{Math.round(r.percentile)}th percentile</p>
          )}
          {r.attention_score != null && (
            <p className="text-sm text-gray-400 flex items-center gap-1.5">
              <Eye size={14} /> Attention {Math.round(r.attention_score)}/100
            </p>
          )}
          {r.points_awarded != null && (
            <Badge tone="green">+{r.points_awarded} points</Badge>
          )}
        </div>
      </div>

      {!published && (
        <div className="rise rounded-2xl border border-gray-800 bg-gray-900 p-5" style={{ "--d": "80ms" }}>
          <p className="text-sm text-gray-400">
            Your paper is in. Full ranking, percentile, and the AI answer-sheet
            analysis publish once the admin closes the championship and reviews
            the results.
          </p>
        </div>
      )}

      {breakdown.length > 0 && (
        <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-2" style={{ "--d": "120ms" }}>
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Topic breakdown</p>
          {breakdown.map((b, i) => (
            <div key={i} className="flex items-center gap-3">
              <span className="text-sm text-gray-300 flex-1">{b.topic || b.name}</span>
              <span className="h-1.5 w-32 rounded-full bg-gray-800 overflow-hidden">
                <span className="block h-full bg-cyan-500" style={{ width: `${Math.round(b.accuracy ?? b.score ?? 0)}%` }} />
              </span>
              <span className="text-xs text-gray-500 tabular-nums w-10 text-right">
                {Math.round(b.accuracy ?? b.score ?? 0)}%
              </span>
            </div>
          ))}
        </div>
      )}

      {practice.length > 0 && (
        <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-2" style={{ "--d": "160ms" }}>
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">What to practice next</p>
          {practice.map((p, i) => (
            <button
              key={i}
              onClick={() => p.topic_id && navigate(`/learn/${p.topic_id}`)}
              className="w-full flex items-center justify-between rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-left hover:border-gray-600 transition group"
            >
              <span className="text-sm text-gray-300">{p.label || p.topic || p}</span>
              {p.topic_id && <ArrowUpRight size={14} className="text-gray-600 group-hover:text-cyan-400" />}
            </button>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <Button onClick={onBackToLobby}>Back to championships</Button>
        <Button variant="outline" onClick={() => navigate("/leaderboard")}>
          View leaderboard
        </Button>
      </div>
    </div>
  );
}