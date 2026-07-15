// DSAGym.jsx - [MOD] topic explainers + practice + hints
// FILE: frontend/src/pages/DSAGym.jsx
// BATCH 27 / v10 DSA Gym (new) - /dsa. Topic-first: pick a DSA topic, read
// its explainer (what/how/when + complexity + patterns), then practice
// problems for that topic at a chosen difficulty in the SAME ArenaWorkspace.
// REPLACES the Placeholder route target from Batch 24.

import React, { useEffect, useState } from "react";
import { ArrowLeft, BookOpen } from "lucide-react";
import arenaApi from "../api/arenaApi";
import ArenaWorkspace from "../components/Arena/ArenaWorkspace";
import { Badge, Button, Spinner } from "../components/Common";

const DIFFICULTIES = ["Easy", "Medium", "Advanced"];

const FALLBACK_TOPICS = [
  "Arrays & Hashing", "Two Pointers", "Sliding Window", "Stack",
  "Binary Search", "Linked List", "Trees", "Tries", "Heaps",
  "Backtracking", "Graphs", "Dynamic Programming", "Greedy",
].map((name, i) => ({ id: `_${i}`, name }));

function normalizeProblem(raw, difficulty) {
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
}

export default function DSAGym() {
  const [topics, setTopics] = useState(null);
  const [topic, setTopic] = useState(null);
  const [explainer, setExplainer] = useState(null);
  const [difficulty, setDifficulty] = useState("Easy");
  const [problem, setProblem] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    arenaApi
      .dsaTopics()
      .then((data) => {
        const list = Array.isArray(data) ? data : data.topics || [];
        setTopics(
          list.length
            ? list.map((t) => ({
                id: t.id,
                name: t.name || t.title,
                pattern_tag: t.pattern_tag,
              }))
            : FALLBACK_TOPICS
        );
      })
      .catch(() => setTopics(FALLBACK_TOPICS));
  }, []);

  const openTopic = async (t) => {
    setTopic(t);
    setExplainer(null);
    setProblem(null);
    if (String(t.id).startsWith("_")) return; // fallback topic, no explainer
    try {
      const data = await arenaApi.dsaTopic(t.id);
      setExplainer(data.explainer || data.content || data);
    } catch (_) {
      /* explainer optional */
    }
  };

  const practice = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await arenaApi.problem({
        category: "dsa",
        difficulty,
        topic: topic.name,
      });
      setProblem(normalizeProblem(data, difficulty));
    } catch (err) {
      setError(
        String(
          err?.response?.data?.detail ||
            "Couldn't load a problem for this topic yet."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  // Solving view
  if (problem) {
    return (
      <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-4">
        <button
          onClick={() => setProblem(null)}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300"
        >
          <ArrowLeft size={16} /> Back to {topic?.name}
        </button>
        <ArenaWorkspace problem={problem} />
      </div>
    );
  }

  // Topic detail view
  if (topic) {
    return (
      <div className="p-4 lg:p-6 max-w-3xl mx-auto space-y-5">
        <button
          onClick={() => setTopic(null)}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300"
        >
          <ArrowLeft size={16} /> All topics
        </button>

        <div className="rise" style={{ "--d": "0ms" }}>
          <h1 className="text-2xl font-bold text-gray-50">{topic.name}</h1>
          {topic.pattern_tag && (
            <Badge tone="cyan">{topic.pattern_tag}</Badge>
          )}
        </div>

        {explainer && (
          <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3" style={{ "--d": "80ms" }}>
            <p className="flex items-center gap-2 text-[11px] uppercase tracking-[0.14em] text-gray-500">
              <BookOpen size={14} /> The idea
            </p>
            {["what", "how", "when", "complexity", "patterns"].map((k) =>
              explainer[k] ? (
                <div key={k}>
                  <p className="text-xs font-semibold text-cyan-400 mb-1 capitalize">{k}</p>
                  <p className="text-sm text-gray-300 whitespace-pre-wrap">
                    {typeof explainer[k] === "string"
                      ? explainer[k]
                      : JSON.stringify(explainer[k])}
                  </p>
                </div>
              ) : null
            )}
            {explainer.content && (
              <p className="text-sm text-gray-300 whitespace-pre-wrap">
                {explainer.content}
              </p>
            )}
          </div>
        )}

        <div className="rise space-y-3" style={{ "--d": "160ms" }}>
          <p className="text-sm font-semibold text-gray-300">Practice</p>
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
          {error && <p className="text-sm text-red-400">{error}</p>}
          <Button onClick={practice} disabled={loading}>
            {loading ? <Spinner size={16} /> : "Get a problem"}
          </Button>
        </div>
      </div>
    );
  }

  // Topic list
  if (!topics) {
    return (
      <div className="h-full flex items-center justify-center">
        <Spinner size={28} />
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-6 max-w-4xl mx-auto space-y-4">
      <div className="rise" style={{ "--d": "0ms" }}>
        <h1 className="text-2xl font-bold text-gray-50">DSA Gym</h1>
        <p className="text-sm text-gray-500 mt-1">
          Learn the pattern first, then drill it. Every problem is tagged with
          the interview pattern it trains.
        </p>
      </div>
      <div className="rise grid sm:grid-cols-2 lg:grid-cols-3 gap-3" style={{ "--d": "80ms" }}>
        {topics.map((t) => (
          <button
            key={t.id}
            onClick={() => openTopic(t)}
            className="text-left rounded-2xl border border-gray-800 bg-gray-900 p-4 transition hover:border-gray-600 hover:-translate-y-0.5 outline-none focus-visible:ring-2 focus-visible:ring-cyan-400"
          >
            <p className="font-semibold text-gray-100">{t.name}</p>
            {t.pattern_tag && (
              <p className="mt-1 text-[11px] text-gray-500">{t.pattern_tag}</p>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}