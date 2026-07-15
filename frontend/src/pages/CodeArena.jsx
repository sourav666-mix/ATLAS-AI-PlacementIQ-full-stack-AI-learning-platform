// CodeArena.jsx - [MOD] category/difficulty + solve loop
// FILE: frontend/src/pages/CodeArena.jsx
// BATCH 27 / v10 Code Arena (new) - /arena. Pick a category + difficulty,
// the backend serves a problem bank-first (generating + caching once on an
// empty cell), then the shared ArenaWorkspace runs the solve loop.
// REPLACES the Placeholder route target from Batch 24.

import React, { useState } from "react";
import { RefreshCw, ArrowLeft } from "lucide-react";
import arenaApi from "../api/arenaApi";
import ArenaWorkspace from "../components/Arena/ArenaWorkspace";
import { Button, Spinner } from "../components/Common";

const CATEGORIES = [
  { id: "dsa", label: "Data Structures & Algorithms" },
  { id: "algorithms", label: "Core Algorithms" },
  { id: "math_ds", label: "Math for Data Science" },
  { id: "sql", label: "Databases & SQL" },
  { id: "ml", label: "ML Fundamentals" },
];
const DIFFICULTIES = ["Easy", "Medium", "Advanced"];

export default function CodeArena() {
  const [category, setCategory] = useState("dsa");
  const [difficulty, setDifficulty] = useState("Easy");
  const [problem, setProblem] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const normalize = (raw) => {
    const p = raw?.problem || raw || {};
    return {
      id: p.id,
      title: p.title,
      difficulty: p.difficulty || difficulty,
      pattern_tag: p.pattern_tag || p.topic,
      source: p.source,
      statement: p.statement || p.description,
      examples: p.examples || p.examples_json || [],
      constraints: p.constraints || p.constraints_json || [],
      hints: p.hints || p.hints_json || [],
      starter_code: p.starter_code || p.starter_code_json || { python: "" },
      optimal_solution: p.optimal_solution,
      complexity: p.complexity,
    };
  };

  const load = async () => {
    setLoading(true);
    setError(null);
    setProblem(null);
    try {
      const data = await arenaApi.problem({ category, difficulty });
      setProblem(normalize(data));
    } catch (err) {
      setError(
        String(
          err?.response?.data?.detail ||
            "Couldn't load a problem. Make sure the arena bank is seeded."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  if (problem) {
    return (
      <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setProblem(null)}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300"
          >
            <ArrowLeft size={16} /> Change problem
          </button>
          <Button size="sm" variant="ghost" onClick={load}>
            <RefreshCw size={13} className="inline mr-1" /> Next problem
          </Button>
        </div>
        <ArenaWorkspace problem={problem} />
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-6 max-w-3xl mx-auto space-y-6">
      <div className="rise" style={{ "--d": "0ms" }}>
        <h1 className="text-2xl font-bold text-gray-50">Code Arena</h1>
        <p className="text-sm text-gray-500 mt-1">
          Pick a category and difficulty. Write, run, submit — get an AI review
          and points on every clean pass.
        </p>
      </div>

      <div className="rise space-y-3" style={{ "--d": "80ms" }}>
        <p className="text-sm font-semibold text-gray-300">Category</p>
        <div className="grid sm:grid-cols-2 gap-2">
          {CATEGORIES.map((c) => (
            <button
              key={c.id}
              onClick={() => setCategory(c.id)}
              className={`text-left rounded-xl border px-4 py-3 text-sm transition ${
                category === c.id
                  ? "border-cyan-600 bg-cyan-950/30 text-cyan-200"
                  : "border-gray-800 bg-gray-900 text-gray-300 hover:border-gray-600"
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      <div className="rise space-y-3" style={{ "--d": "160ms" }}>
        <p className="text-sm font-semibold text-gray-300">Difficulty</p>
        <div className="flex gap-2">
          {DIFFICULTIES.map((d) => (
            <button
              key={d}
              onClick={() => setDifficulty(d)}
              className={`px-4 py-2 rounded-xl border text-sm transition ${
                difficulty === d
                  ? "border-cyan-600 bg-cyan-950/30 text-cyan-200"
                  : "border-gray-800 bg-gray-900 text-gray-300 hover:border-gray-600"
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="rise" style={{ "--d": "240ms" }}>
        <Button size="lg" onClick={load} disabled={loading}>
          {loading ? <Spinner size={16} /> : "Start solving"}
        </Button>
      </div>
    </div>
  );
}