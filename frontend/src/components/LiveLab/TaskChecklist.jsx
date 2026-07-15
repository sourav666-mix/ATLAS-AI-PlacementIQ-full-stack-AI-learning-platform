// FILE: frontend/src/components/LiveLab/TaskChecklist.jsx
// BATCH 21 / v11 Phase 13 (new) - Graded lab steps. "Check my work" runs the
// HIDDEN tests inside the student's Pyodide (same namespace their code just
// ran in), then reports pass/fail to POST /lab/grade. Deterministic — the
// grade path involves NO AI anywhere. Completion posts /lab/complete and
// points flow through progress_engine on the backend.

import React, { useState } from "react";
import labApi from "../../api/labApi";
import useLabStore from "../../store/labStore";

export default function TaskChecklist({ pyodide }) {
  const {
    lab, code, taskResults, grading, completed, pointsAwarded,
    setGrading, setTaskResults, markCompleted,
  } = useLabStore();
  const [error, setError] = useState(null);

  if (!lab) return null;
  const tasks = lab.graded_tasks || [];
  const passedCount = tasks.filter((t) => taskResults[t.id]).length;
  const allPassed = tasks.length > 0 && passedCount === tasks.length;

  const checkMyWork = async () => {
    setError(null);
    setGrading(true);
    try {
      // 1. Make sure the student's current code has run (fresh namespace)
      const run = await pyodide.runCode(code);
      if (!run.ok) {
        setError("Your code has an error — fix it before grading.");
        return;
      }
      // 2. Hidden tests execute IN THE BROWSER
      const tests = await labApi.tests(lab.id);
      const { results } = await pyodide.runTests(tests);
      setTaskResults(results);
      // 3. Record pass/fail on the backend (metadata + code text only)
      await labApi.grade(lab.id, results, code);
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message || err));
    } finally {
      setGrading(false);
    }
  };

  const finishLab = async () => {
    setError(null);
    try {
      const res = await labApi.complete(lab.id);
      markCompleted(res.points_awarded || 0);
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message || err));
    }
  };

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-200">
          Graded tasks ({passedCount}/{tasks.length})
        </h3>
        {completed && (
          <span className="text-xs px-2 py-1 rounded-full bg-emerald-900 text-emerald-300">
            Completed · +{pointsAwarded} pts
          </span>
        )}
      </div>

      <ul className="space-y-2">
        {tasks.map((task) => {
          const passed = !!taskResults[task.id];
          return (
            <li key={task.id} className="flex items-start gap-2 text-sm">
              <span
                className={`mt-0.5 h-4 w-4 rounded-full flex items-center justify-center text-[10px] ${
                  passed
                    ? "bg-emerald-500 text-gray-950"
                    : "bg-gray-700 text-gray-400"
                }`}
              >
                {passed ? "✓" : "•"}
              </span>
              <span className={passed ? "text-gray-300" : "text-gray-400"}>
                {task.title || task.id}
                {task.points ? (
                  <span className="text-gray-600"> · {task.points} pts</span>
                ) : null}
              </span>
            </li>
          );
        })}
      </ul>

      {error && <p className="text-xs text-red-400">{error}</p>}

      <div className="flex gap-2">
        <button
          onClick={checkMyWork}
          disabled={grading || !pyodide.ready || completed}
          className="flex-1 px-3 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white font-medium"
        >
          {grading ? "Grading in your browser…" : "Check my work"}
        </button>
        {allPassed && !completed && (
          <button
            onClick={finishLab}
            className="flex-1 px-3 py-2 text-sm rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
          >
            Finish lab → claim points
          </button>
        )}
      </div>
      <p className="text-[11px] text-gray-600">
        Grading runs hidden tests on your machine — no AI, no upload of your
        dataset. Only pass/fail and your code text are recorded.
      </p>
    </div>
  );
}