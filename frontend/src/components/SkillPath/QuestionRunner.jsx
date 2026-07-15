// QuestionRunner.jsx - [NEW] attempt-first question loop
// FILE: frontend/src/components/SkillPath/QuestionRunner.jsx
// BATCH 26 / v10 SkillPath (new) - The attempt-first loop, enforced in UI:
//   1. Pick a question (grouped Basic / Medium / Advanced)
//   2. Write YOUR answer  ->  Score my answer (the ONE AI call)
//   3. Score + feedback come back; ONLY NOW does "Show model answer" appear
//   4. Reveal is a bank read (no AI). Re-attempts train but don't farm points.
// There is deliberately no way to see the model answer before attempting.

import React, { useMemo, useState } from "react";
import { Send, Eye, RotateCcw } from "lucide-react";
import practiceApi from "../../api/practiceApi";
import RevealCard from "./RevealCard";
import { Badge, Button, Spinner } from "../Common";

const LEVELS = [
  { key: "basic", label: "Basic", tone: "cyan" },
  { key: "medium", label: "Medium", tone: "amber" },
  { key: "advanced", label: "Advanced", tone: "red" },
];

function levelOf(question) {
  const d = String(question.difficulty || "").toLowerCase();
  if (d.startsWith("adv")) return "advanced";
  if (d.startsWith("med") || d.startsWith("int")) return "medium";
  return "basic";
}

function scoreTone(score) {
  if (score >= 8) return "text-emerald-400";
  if (score >= 5) return "text-amber-400";
  return "text-red-400";
}

export default function QuestionRunner({ questions = [], onScored }) {
  const [level, setLevel] = useState("basic");
  const [current, setCurrent] = useState(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);   // {score, feedback}
  const [reveal, setReveal] = useState(null);
  const [revealBusy, setRevealBusy] = useState(false);
  const [error, setError] = useState(null);
  const [scoredIds, setScoredIds] = useState({}); // id -> score

  const grouped = useMemo(() => {
    const g = { basic: [], medium: [], advanced: [] };
    questions.forEach((q) => g[levelOf(q)].push(q));
    return g;
  }, [questions]);

  const open = (question) => {
    setCurrent(question);
    setAnswer("");
    setResult(null);
    setReveal(null);
    setError(null);
  };

  const submit = async () => {
    if (!current || !answer.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const data = await practiceApi.attempt(current.id, answer.trim());
      const score = Number(data.score ?? data.result?.score ?? 0);
      const feedback =
        data.feedback || data.result?.feedback || "Scored.";
      setResult({ score, feedback });
      setScoredIds((prev) => ({ ...prev, [current.id]: score }));
      if (onScored) onScored(current.id, score);
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally {
      setBusy(false);
    }
  };

  const doReveal = async () => {
    if (!current || revealBusy) return;
    setRevealBusy(true);
    try {
      setReveal(await practiceApi.reveal(current.id));
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally {
      setRevealBusy(false);
    }
  };

  // ---- Question list view ----
  if (!current) {
    const list = grouped[level];
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">
            Practice — attempt first, always
          </p>
          <div className="flex gap-1">
            {LEVELS.map((l) => (
              <button
                key={l.key}
                onClick={() => setLevel(l.key)}
                className={`px-3 py-1 rounded-lg text-xs transition ${
                  level === l.key
                    ? "bg-gray-800 text-gray-100"
                    : "text-gray-500 hover:text-gray-300"
                }`}
              >
                {l.label}
                <span className="ml-1 text-gray-600 tabular-nums">
                  {grouped[l.key].length}
                </span>
              </button>
            ))}
          </div>
        </div>

        {list.length === 0 ? (
          <p className="text-sm text-gray-500">
            No {level} questions seeded for this subtopic yet.
          </p>
        ) : (
          <div className="space-y-2">
            {list.map((q, index) => {
              const scored = scoredIds[q.id];
              return (
                <button
                  key={q.id}
                  onClick={() => open(q)}
                  className="w-full flex items-center gap-3 rounded-xl border border-gray-800 bg-gray-950 px-4 py-3 text-left transition hover:border-gray-600 outline-none focus-visible:ring-2 focus-visible:ring-cyan-400"
                >
                  <span className="text-[11px] text-gray-600 tabular-nums w-5">
                    {index + 1}
                  </span>
                  <span className="flex-1 text-sm text-gray-300 line-clamp-2">
                    {q.question_text || q.question || q.prompt}
                  </span>
                  {scored != null && (
                    <span className={`text-xs font-bold tabular-nums ${scoreTone(scored)}`}>
                      {scored}/10
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  // ---- Single question: attempt-first flow ----
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm text-gray-100 leading-relaxed flex-1">
          {current.question_text || current.question || current.prompt}
        </p>
        <Badge tone={LEVELS.find((l) => l.key === levelOf(current))?.tone}>
          {levelOf(current)}
        </Badge>
      </div>

      <textarea
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        placeholder="Write your answer in your own words — that's what gets scored."
        rows={5}
        disabled={busy}
        className="w-full bg-gray-950 border border-gray-800 rounded-xl px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-cyan-700 resize-y"
      />

      {error && <p className="text-xs text-red-400">{error}</p>}

      {result && (
        <div className="rounded-xl border border-gray-800 bg-gray-950 p-4 space-y-2">
          <p className={`text-2xl font-bold tabular-nums ${scoreTone(result.score)}`}>
            {result.score}
            <span className="text-sm text-gray-500 font-medium"> / 10</span>
          </p>
          <p className="text-sm text-gray-300 leading-relaxed">{result.feedback}</p>
        </div>
      )}

      {reveal && <RevealCard reveal={reveal} />}

      <div className="flex flex-wrap gap-2">
        {!result ? (
          <Button onClick={submit} disabled={busy || !answer.trim()}>
            {busy ? <Spinner size={14} /> : <><Send size={14} className="inline mr-1.5" />Score my answer</>}
          </Button>
        ) : (
          <>
            {!reveal && (
              <Button variant="success" onClick={doReveal} disabled={revealBusy}>
                {revealBusy ? <Spinner size={14} /> : <><Eye size={14} className="inline mr-1.5" />Show model answer</>}
              </Button>
            )}
            <Button
              variant="ghost"
              onClick={() => { setAnswer(""); setResult(null); setReveal(null); }}
            >
              <RotateCcw size={14} className="inline mr-1.5" />
              Try again (trains, doesn't re-score points)
            </Button>
          </>
        )}
        <Button variant="outline" onClick={() => setCurrent(null)}>
          Back to questions
        </Button>
      </div>
    </div>
  );
}