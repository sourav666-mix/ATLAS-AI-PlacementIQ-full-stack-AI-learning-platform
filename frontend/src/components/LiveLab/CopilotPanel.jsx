// FILE: frontend/src/components/LiveLab/CopilotPanel.jsx
// BATCH 22 / v11 Phase 15 (new) - The AI copilot UI: explain / suggest /
// fix / review over the Batch 20 bounded Type-B endpoints. Rules honoured
// here: FIX proposes a corrected snippet with an accept-or-not choice —
// NEVER auto-applied (the student keeps learning); the daily-cap counter is
// always visible; cached answers are labelled (they cost nothing).

import React, { useMemo, useState } from "react";
import labApi from "../../api/labApi";
import useLabStore from "../../store/labStore";

const MODES = [
  { id: "explain", label: "Explain error" },
  { id: "suggest", label: "What next?" },
  { id: "fix", label: "Fix my code" },
  { id: "review", label: "Review" },
];

export default function CopilotPanel({ pyodide }) {
  const { lab, code, setCode, datasetName } = useLabStore();
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null); // {mode, answer, cached, calls_left_today}
  const [error, setError] = useState(null);

  // The most recent stderr line is the "current error" context
  const lastError = useMemo(() => {
    const errs = (pyodide.output || []).filter((l) => l.kind === "stderr");
    return errs.length ? errs[errs.length - 1].text : "";
  }, [pyodide.output]);

  const ask = async (mode) => {
    if (!lab || busy) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await labApi.copilot(mode, {
        lab_id: lab.id,
        code,
        error: lastError || undefined,
        question: question || undefined,
        dataset_shape: datasetName ? `file: ${datasetName}` : undefined,
      });
      setResult(res);
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message || err));
    } finally {
      setBusy(false);
    }
  };

  // For 'fix' answers: extract the code part (before the WHY: line)
  const fixParts = useMemo(() => {
    if (!result || result.mode !== "fix") return null;
    const idx = result.answer.indexOf("WHY:");
    return {
      snippet:
        idx >= 0 ? result.answer.slice(0, idx).trim() : result.answer.trim(),
      why: idx >= 0 ? result.answer.slice(idx).trim() : "",
    };
  }, [result]);

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-200">AI Copilot</h3>
        {result && result.calls_left_today != null && (
          <span className="text-[11px] text-gray-500">
            {result.cached ? "cached · free" : `${result.calls_left_today} calls left today`}
          </span>
        )}
      </div>

      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Optional: your question…"
        className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-cyan-700"
      />

      <div className="grid grid-cols-2 gap-2">
        {MODES.map((m) => (
          <button
            key={m.id}
            onClick={() => ask(m.id)}
            disabled={busy || !lab}
            className="px-2 py-1.5 text-xs rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-40 text-gray-200"
          >
            {busy ? "…" : m.label}
          </button>
        ))}
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {result && result.mode !== "fix" && (
        <pre className="whitespace-pre-wrap text-xs text-gray-300 bg-gray-950 border border-gray-800 rounded-lg p-3 max-h-48 overflow-y-auto">
          {result.answer}
        </pre>
      )}

      {fixParts && (
        <div className="space-y-2">
          <pre className="whitespace-pre-wrap text-xs text-emerald-300 bg-gray-950 border border-emerald-900 rounded-lg p-3 max-h-48 overflow-y-auto">
            {fixParts.snippet}
          </pre>
          {fixParts.why && (
            <p className="text-xs text-gray-400">{fixParts.why}</p>
          )}
          <div className="flex gap-2">
            <button
              onClick={() => {
                setCode(fixParts.snippet);
                setResult(null);
              }}
              className="flex-1 px-2 py-1.5 text-xs rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white"
            >
              Accept → replace editor
            </button>
            <button
              onClick={() => setResult(null)}
              className="flex-1 px-2 py-1.5 text-xs rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300"
            >
              Keep my code
            </button>
          </div>
        </div>
      )}

      <p className="text-[11px] text-gray-600">
        The copilot teaches — it won't hand over graded answers. Fixes are
        never auto-applied.
      </p>
    </div>
  );
}