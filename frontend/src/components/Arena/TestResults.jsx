// TestResults.jsx - [NEW] visible/hidden test output
// FILE: frontend/src/components/Arena/TestResults.jsx
// BATCH 27 / v10 Code Arena (new) - LeetCode-style test output. Shows each
// visible case with expected vs actual; hidden cases show pass/fail counts
// only (never the hidden inputs). Compile/runtime errors render raw.

import React from "react";
import { Check, X } from "lucide-react";

export default function TestResults({ result }) {
  if (!result) return null;

  if (result.error) {
    return (
      <div className="rounded-xl border border-red-900 bg-red-950/30 p-4">
        <p className="text-xs font-semibold text-red-400 mb-1">
          {result.error_type || "Error"}
        </p>
        <pre className="text-xs text-red-300 whitespace-pre-wrap font-mono">
          {result.error}
        </pre>
      </div>
    );
  }

  const cases = result.cases || result.visible || [];
  const passed = result.passed_count ?? cases.filter((c) => c.passed).length;
  const total = result.total ?? cases.length;
  const allPass = result.passed ?? (total > 0 && passed === total);

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-950 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <p className={`text-sm font-semibold ${allPass ? "text-emerald-400" : "text-amber-400"}`}>
          {allPass ? "All tests passed" : `${passed}/${total} tests passed`}
        </p>
        {result.runtime_ms != null && (
          <span className="text-xs text-gray-600 tabular-nums">
            {result.runtime_ms} ms
          </span>
        )}
      </div>

      <div className="space-y-2">
        {cases.map((c, i) => (
          <div
            key={i}
            className={`rounded-lg border p-3 text-xs font-mono ${
              c.passed
                ? "border-emerald-900/50 bg-emerald-950/20"
                : "border-red-900/50 bg-red-950/20"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              {c.passed ? (
                <Check size={13} className="text-emerald-400" />
              ) : (
                <X size={13} className="text-red-400" />
              )}
              <span className="text-gray-400">Case {i + 1}</span>
            </div>
            {c.hidden ? (
              <p className="text-gray-500">Hidden test</p>
            ) : (
              <div className="space-y-0.5 text-gray-300">
                {c.input != null && <p><span className="text-gray-500">in: </span>{String(c.input)}</p>}
                {c.expected != null && <p><span className="text-gray-500">expected: </span>{String(c.expected)}</p>}
                {c.actual != null && <p><span className="text-gray-500">got: </span>{String(c.actual)}</p>}
              </div>
            )}
          </div>
        ))}
        {result.hidden_passed != null && (
          <p className="text-xs text-gray-500">
            Hidden tests: {result.hidden_passed}/{result.hidden_total} passed
          </p>
        )}
      </div>
    </div>
  );
}