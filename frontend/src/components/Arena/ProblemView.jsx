// ProblemView.jsx - [NEW] problem statement + 2 examples
// FILE: frontend/src/components/Arena/ProblemView.jsx
// BATCH 27 / v10 Code Arena (new) - The problem statement pane: title,
// difficulty, pattern tag, statement, the 2 worked examples, constraints.
// Read-only, pure DB content — no AI, no cost.

import React from "react";
import { Badge } from "../Common";

function toList(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === "string") return value.split("\n").filter(Boolean);
  return Object.values(value);
}

export default function ProblemView({ problem }) {
  if (!problem) return null;
  const diff = String(problem.difficulty || "Easy");
  const tone = diff.toLowerCase().startsWith("adv")
    ? "red"
    : diff.toLowerCase().startsWith("med")
    ? "amber"
    : "green";
  const examples = toList(problem.examples);
  const constraints = toList(problem.constraints);

  return (
    <div className="h-full overflow-y-auto bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
      <div className="flex items-center gap-2 flex-wrap">
        <Badge tone={tone}>{diff}</Badge>
        {problem.pattern_tag && <Badge tone="cyan">{problem.pattern_tag}</Badge>}
        {problem.source === "auto" && <Badge>fresh from bank</Badge>}
      </div>

      <h2 className="text-lg font-bold text-gray-50">{problem.title}</h2>

      <p className="text-sm leading-relaxed text-gray-300 whitespace-pre-wrap">
        {problem.statement}
      </p>

      {examples.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-cyan-400">Examples</p>
          {examples.map((ex, i) => {
            const input = ex.input ?? ex.in ?? null;
            const output = ex.output ?? ex.out ?? null;
            return (
              <div
                key={i}
                className="rounded-lg bg-gray-950 border border-gray-800 p-3 text-xs font-mono text-gray-300 space-y-1"
              >
                {input != null ? (
                  <>
                    <p><span className="text-gray-500">Input: </span>{String(input)}</p>
                    <p><span className="text-gray-500">Output: </span>{String(output)}</p>
                    {ex.explanation && (
                      <p className="text-gray-500 font-sans">{ex.explanation}</p>
                    )}
                  </>
                ) : (
                  <p>{typeof ex === "string" ? ex : JSON.stringify(ex)}</p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {constraints.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-cyan-400 mb-1">Constraints</p>
          <ul className="text-xs text-gray-400 font-mono space-y-0.5">
            {constraints.map((c, i) => (
              <li key={i}>• {typeof c === "string" ? c : JSON.stringify(c)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}