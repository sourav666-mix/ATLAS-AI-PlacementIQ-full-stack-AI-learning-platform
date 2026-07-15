// FILE: frontend/src/components/Arena/ArenaWorkspace.jsx
// BATCH 27 / v10 Code Arena + DSA (new) - The shared solve environment used
// by BOTH Code Arena and DSA Gym: statement | editor on top, results / hints
// / AI review below. RUN executes visible tests (Python runs instantly in
// the browser via the Pyodide worker; other languages go to the server);
// SUBMIT always posts to the server for hidden tests + AI review + points.

import React, { useCallback, useState } from "react";
import arenaApi from "../../api/arenaApi";
import usePyodide from "../../hooks/usePyodide";
import ProblemView from "./ProblemView";
import CodePanel from "./CodePanel";
import TestResults from "./TestResults";
import HintLadder from "./HintLadder";
import AIReviewCard from "./AIReviewCard";

// Build a Python harness that runs visible cases locally in Pyodide. Expects
// the problem to expose a `solution` entrypoint; if we can't tell, we skip
// local run and defer to the server (returned as {localUnsupported:true}).
function buildLocalHarness(code, problem) {
  const cases = (problem?.examples || []).filter(
    (e) => e && e.input != null && e.output != null
  );
  if (!cases.length) return null;
  const fnMatch = code.match(/def\s+([a-zA-Z_]\w*)\s*\(/);
  if (!fnMatch) return null;
  const fn = fnMatch[1];
  const payload = JSON.stringify(
    cases.map((c) => ({ input: c.input, output: String(c.output) }))
  );
  return `
${code}

import json as _json
_cases = _json.loads(r'''${payload}''')
_results = []
for _c in _cases:
    try:
        _in = _c["input"]
        try:
            _parsed = _json.loads(_in) if isinstance(_in, str) else _in
        except Exception:
            _parsed = _in
        _got = ${fn}(_parsed) if not isinstance(_parsed, (list, tuple)) else ${fn}(*_parsed) if isinstance(_parsed, list) and len(_parsed) and False else ${fn}(_parsed)
        _ok = str(_got).strip() == str(_c["output"]).strip()
        _results.append({"input": _c["input"], "expected": _c["output"], "actual": str(_got), "passed": _ok})
    except Exception as _e:
        _results.append({"input": _c["input"], "expected": _c["output"], "actual": "ERROR: " + str(_e), "passed": False})
print("__ATLAS_RESULTS__" + _json.dumps(_results))
`;
}

export default function ArenaWorkspace({ problem, onSolved }) {
  const pyodide = usePyodide();
  const [running, setRunning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [review, setReview] = useState(null);
  const [points, setPoints] = useState(0);
  const [error, setError] = useState(null);

  const run = useCallback(
    async (language, code) => {
      setRunning(true);
      setError(null);
      setReview(null);
      try {
        // Fast path: Python runs locally in the browser worker.
        if (language === "python") {
          const harness = buildLocalHarness(code, problem);
          if (harness) {
            pyodide.clearOutput();
            const res = await pyodide.runCode(harness);
            const line = (pyodide.output || [])
              .map((l) => l.text || "")
              .join("\n")
              .split("\n")
              .find((t) => t.includes("__ATLAS_RESULTS__"));
            if (res.ok && line) {
              const cases = JSON.parse(line.replace("__ATLAS_RESULTS__", ""));
              setTestResult({
                cases,
                passed_count: cases.filter((c) => c.passed).length,
                total: cases.length,
                runtime_ms: res.ms,
              });
              return;
            }
            if (!res.ok) {
              setTestResult({ error: res.error, error_type: "Runtime error" });
              return;
            }
          }
        }
        // Fallback: server sandbox runs visible tests.
        const data = await arenaApi.run(problem.id, language, code);
        setTestResult(data);
      } catch (err) {
        setError(String(err?.response?.data?.detail || err.message));
      } finally {
        setRunning(false);
      }
    },
    [problem, pyodide]
  );

  const submit = useCallback(
    async (language, code) => {
      setSubmitting(true);
      setError(null);
      try {
        const data = await arenaApi.submit(problem.id, language, code);
        setTestResult(data.tests || data.test_result || data);
        setReview(data.review || data.ai_review || null);
        const awarded = Number(data.points_awarded ?? data.points ?? 0);
        setPoints(awarded);
        if ((data.passed ?? data.tests?.passed) && onSolved) onSolved(awarded);
      } catch (err) {
        setError(String(err?.response?.data?.detail || err.message));
      } finally {
        setSubmitting(false);
      }
    },
    [problem, onSolved]
  );

  if (!problem) return null;

  return (
    <div className="space-y-4">
      <div className="grid lg:grid-cols-2 gap-4 min-h-[440px]">
        <div className="rise" style={{ "--d": "0ms" }}>
          <ProblemView problem={problem} />
        </div>
        <div className="rise h-full" style={{ "--d": "80ms" }}>
          <CodePanel
            problem={problem}
            onRun={run}
            onSubmit={submit}
            running={running}
            submitting={submitting}
          />
        </div>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="grid lg:grid-cols-2 gap-4 items-start">
        <div className="space-y-4">
          {testResult && <TestResults result={testResult} />}
          {review && <AIReviewCard review={review} pointsAwarded={points} />}
        </div>
        <HintLadder
          hints={problem.hints}
          optimal={problem.optimal_solution}
          complexity={problem.complexity}
        />
      </div>
    </div>
  );
}