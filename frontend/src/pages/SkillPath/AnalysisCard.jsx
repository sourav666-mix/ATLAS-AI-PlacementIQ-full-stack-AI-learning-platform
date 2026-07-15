// frontend/src/components/SkillPath/AnalysisCard.jsx
/**
 * ATLAS AI 4.0 - v12 SkillPath: STEP 8's result surface.
 * Verdict + score, what was good / missing, the walkthrough and model
 * solution (revealed ONLY after submission), the next hint, points, and
 * the two deterministic celebration banners (subtopic tick / topic green).
 */

const VERDICT_STYLE = {
  correct: { label: "Correct", cls: "bg-emerald-950/50 text-emerald-300 border-emerald-700" },
  partially_correct: { label: "Partially correct", cls: "bg-amber-950/50 text-amber-300 border-amber-700" },
  incorrect: { label: "Not yet", cls: "bg-red-950/50 text-red-300 border-red-700" },
};

export default function AnalysisCard({ analysis, onNext, nextLabel = "Next question →" }) {
  if (!analysis) return null;
  const v = VERDICT_STYLE[analysis.verdict] || VERDICT_STYLE.incorrect;

  return (
    <div className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      <div className="flex flex-wrap items-center gap-3">
        <span className={`rounded-md border px-2 py-1 text-xs font-semibold ${v.cls}`}>
          {v.label}
        </span>
        <span className="text-sm text-zinc-300">
          score <span className="font-bold text-zinc-100">{analysis.score}</span>/100
        </span>
        {analysis.points_awarded > 0 && (
          <span className="text-sm text-amber-300">+{analysis.points_awarded} pts</span>
        )}
      </div>

      {analysis.subtopic_mastered && (
        <p className="rounded-md bg-emerald-950/50 px-3 py-2 text-sm text-emerald-300">
          ✅ Skill mastered - this tab just got its green tick.
        </p>
      )}
      {analysis.topic_complete && (
        <p className="rounded-md bg-emerald-950/60 px-3 py-2 text-sm font-semibold text-emerald-200">
          🏆 Topic complete - it turns green on your roadmap.
        </p>
      )}

      {analysis.good?.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase text-emerald-400">What you did well</h3>
          <ul className="mt-1 space-y-1 text-sm text-zinc-300">
            {analysis.good.map((g, i) => <li key={i}>• {g}</li>)}
          </ul>
        </div>
      )}

      {analysis.missing?.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase text-amber-400">What was missing</h3>
          <ul className="mt-1 space-y-1 text-sm text-zinc-300">
            {analysis.missing.map((m, i) => <li key={i}>• {m}</li>)}
          </ul>
        </div>
      )}

      {analysis.walkthrough && (
        <div>
          <h3 className="text-xs font-semibold uppercase text-sky-400">Walkthrough</h3>
          <p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-zinc-300">
            {analysis.walkthrough}
          </p>
        </div>
      )}

      {analysis.model_solution && (
        <details className="rounded-md border border-zinc-800 bg-zinc-950/60">
          <summary className="cursor-pointer px-3 py-2 text-sm text-zinc-200">
            Model solution
          </summary>
          <pre className="overflow-auto px-3 pb-3 font-mono text-xs text-sky-200 whitespace-pre-wrap">
            {analysis.model_solution}
          </pre>
        </details>
      )}

      {analysis.next_hint && (
        <p className="rounded-md bg-sky-950/40 px-3 py-2 text-sm text-sky-300">
          💡 {analysis.next_hint}
        </p>
      )}

      <button type="button" onClick={onNext}
        className="w-full rounded-lg bg-sky-600 py-2.5 text-sm font-semibold
                   text-white hover:bg-sky-500">
        {nextLabel}
      </button>
    </div>
  );
}