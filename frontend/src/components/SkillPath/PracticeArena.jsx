// FILE: frontend/src/components/SkillPath/PracticeArena.jsx
// v12 — the 25-question AI-adaptive loop. Question -> attempt -> AI analysis -> next.
// "Next" stays locked until an attempt is submitted (attempt-first rule).
import React, { useCallback, useEffect, useState } from "react";
import {
  getPracticeQuestion,
  submitAttempt,
  revealAnswer,
} from "../../api/skillpathV3Api";

const TIER = {
  basic: "bg-emerald-500/10 text-emerald-300",
  medium: "bg-amber-500/10 text-amber-300",
  advanced: "bg-red-500/10 text-red-300",
};

export default function PracticeArena({ subtopicId, subtopicName, onExit }) {
  const [position, setPosition] = useState(1);
  const [question, setQuestion] = useState(null);
  const [answer, setAnswer] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [reveal, setReveal] = useState(null);
  const [busy, setBusy] = useState(false);
  const [counter, setCounter] = useState(0);
  const [err, setErr] = useState(null);

  const load = useCallback(async () => {
    setBusy(true);
    setErr(null);
    setAnalysis(null);
    setReveal(null);
    setAnswer("");
    try {
      const q = await getPracticeQuestion(subtopicId, position);
      setQuestion(q);
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Failed to load question");
    } finally {
      setBusy(false);
    }
  }, [subtopicId, position]);

  useEffect(() => {
    load();
  }, [load]);

  const onSubmit = async () => {
    if (!answer.trim()) return;
    setBusy(true);
    setErr(null);
    try {
      const res = await submitAttempt(question.question_id, answer);
      setAnalysis(res);
      setCounter(res.counter ?? 0);
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Attempt failed");
    } finally {
      setBusy(false);
    }
  };

  const onReveal = async () => {
    try {
      setReveal(await revealAnswer(question.question_id));
    } catch (e) {
      setErr("Could not reveal answer");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <button onClick={onExit} className="text-sm text-gray-400 hover:text-gray-200">
          ← Learn Card
        </button>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400">
            {subtopicName} · Question {position} of 25
          </span>
          <div className="h-2 w-32 rounded-full bg-gray-800 overflow-hidden">
            <div
              className="h-full bg-violet-500 transition-all"
              style={{ width: `${(counter / 25) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {err && <p className="text-red-400">{err}</p>}
      {busy && !question && <p className="text-gray-500">Loading question…</p>}

      {question && (
        <>
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
            <span
              className={`text-xs rounded px-2 py-0.5 ${TIER[question.difficulty_tier] || ""}`}
            >
              {question.difficulty_tier}
            </span>
            <p className="mt-3 text-gray-100 whitespace-pre-wrap leading-relaxed">
              {question.statement}
            </p>
            {question.constraints && (
              <p className="mt-2 text-sm text-gray-500">
                Constraints: {question.constraints}
              </p>
            )}
            <div className="mt-4 grid sm:grid-cols-2 gap-3">
              {(question.examples || []).slice(0, 2).map((ex, i) => (
                <div key={i} className="rounded-lg bg-gray-950 border border-gray-800 p-3">
                  <p className="text-xs text-gray-500">Example {i + 1}</p>
                  <p className="mt-1 text-sm text-gray-300 whitespace-pre-wrap">{ex.prompt}</p>
                  <pre className="mt-1 text-sm text-emerald-300 whitespace-pre-wrap overflow-x-auto">
                    {ex.solution}
                  </pre>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Write your answer…"
              spellCheck={false}
              className="w-full h-44 bg-gray-950 p-4 text-gray-100 outline-none resize-none font-mono text-sm"
            />
            <div className="flex items-center justify-between border-t border-gray-800 px-4 py-3">
              <button
                onClick={onSubmit}
                disabled={busy || !answer.trim() || !!analysis}
                className="rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-40 px-4 py-1.5 text-sm font-medium text-white"
              >
                {busy ? "Checking…" : "Submit attempt"}
              </button>
              {analysis && (
                <button
                  onClick={onReveal}
                  className="text-sm text-gray-400 hover:text-gray-200"
                >
                  Reveal full answer
                </button>
              )}
            </div>
          </div>

          {analysis && (
            <div className="rounded-xl border border-violet-500/30 bg-violet-500/5 p-5 space-y-2">
              <p className="font-medium text-violet-200">Verdict: {analysis.verdict}</p>
              {analysis.whats_good && (
                <p className="text-sm text-emerald-300">Good: {analysis.whats_good}</p>
              )}
              {analysis.whats_missing && (
                <p className="text-sm text-amber-300">Missing: {analysis.whats_missing}</p>
              )}
              {analysis.hint && (
                <p className="text-sm text-gray-300">Hint: {analysis.hint}</p>
              )}
              {analysis.followup && (
                <p className="text-sm text-red-300">Follow-up: {analysis.followup}</p>
              )}
            </div>
          )}

          {reveal && (
            <div className="rounded-xl border border-gray-800 bg-gray-950 p-5 space-y-2 text-sm">
              <p className="font-medium text-gray-200">Model answer</p>
              <pre className="text-emerald-300 whitespace-pre-wrap overflow-x-auto">
                {reveal.model_answer}
              </pre>
              {reveal.common_mistakes && (
                <p className="text-gray-400">Common mistakes: {reveal.common_mistakes}</p>
              )}
            </div>
          )}

          <div className="flex justify-end">
            <button
              onClick={() => (position >= 25 ? onExit() : setPosition((p) => p + 1))}
              disabled={!analysis}
              className="rounded-lg bg-gray-100 text-gray-900 disabled:opacity-30 px-5 py-2 text-sm font-semibold"
            >
              {position >= 25 ? "Finish" : "Next question →"}
            </button>
          </div>
        </>
      )}
    </div>
  );
}