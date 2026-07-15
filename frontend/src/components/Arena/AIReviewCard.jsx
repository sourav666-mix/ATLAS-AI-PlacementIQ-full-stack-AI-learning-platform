// AIReviewCard.jsx - [NEW] correctness + complexity + optimal solution
// FILE: frontend/src/components/Arena/AIReviewCard.jsx
// BATCH 27 / v10 Code Arena (new) - The AI review returned on SUBMIT:
// correctness verdict, time/space complexity, what's suboptimal, the optimal
// solution, and edge cases missed. This is the ONE AI call in the loop.

import React from "react";
import { Sparkles, CheckCircle2, XCircle } from "lucide-react";

export default function AIReviewCard({ review, pointsAwarded }) {
  if (!review) return null;
  const correct = review.correct ?? review.passed ?? null;
  const missed = review.edge_cases_missed || review.missed_edge_cases || [];

  return (
    <div className="rounded-2xl border border-cyan-900/60 bg-cyan-950/15 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <p className="flex items-center gap-2 text-[11px] uppercase tracking-[0.14em] text-cyan-400">
          <Sparkles size={14} /> AI review
        </p>
        {pointsAwarded > 0 && (
          <span className="text-xs font-semibold text-emerald-400">
            +{pointsAwarded} pts
          </span>
        )}
      </div>

      {correct != null && (
        <div className={`flex items-center gap-2 text-sm font-semibold ${correct ? "text-emerald-400" : "text-amber-400"}`}>
          {correct ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
          {correct ? "Correct solution" : "Not fully correct yet"}
        </div>
      )}

      {(review.time_complexity || review.complexity) && (
        <p className="text-sm text-gray-300">
          <span className="text-gray-500">Complexity: </span>
          <span className="font-mono">
            {review.time_complexity || review.complexity}
            {review.space_complexity ? ` time · ${review.space_complexity} space` : ""}
          </span>
        </p>
      )}

      {review.feedback && (
        <div>
          <p className="text-xs font-semibold text-cyan-300 mb-1">What could be better</p>
          <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
            {review.feedback || review.suboptimal}
          </p>
        </div>
      )}

      {missed.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-amber-300 mb-1">Edge cases missed</p>
          <ul className="text-sm text-gray-300 space-y-0.5">
            {missed.map((m, i) => (
              <li key={i}>• {typeof m === "string" ? m : JSON.stringify(m)}</li>
            ))}
          </ul>
        </div>
      )}

      {review.optimal_solution && (
        <div>
          <p className="text-xs font-semibold text-emerald-300 mb-1">Optimal solution</p>
          <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono bg-gray-950 border border-gray-800 rounded-lg p-3 overflow-x-auto">
            {review.optimal_solution}
          </pre>
        </div>
      )}
    </div>
  );
}