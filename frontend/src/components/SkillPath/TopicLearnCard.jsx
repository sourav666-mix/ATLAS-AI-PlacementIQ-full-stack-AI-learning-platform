// FILE: frontend/src/components/SkillPath/TopicLearnCard.jsx
// v12 Learn Mode — what / when / how + 5 worked examples + visualization.
// "Practice This Subtopic" is the ONLY door into the 25-question arena.
import React, { useEffect, useState } from "react";
import { getLearnCard } from "../../api/skillpathV3Api";
import VisualizationBlock from "./VisualizationBlock";
import PracticeArena from "./PracticeArena";

function Block({ title, children }) {
  if (!children) return null;
  return (
    <section className="rounded-xl border border-gray-800 bg-gray-900 p-5">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-violet-400">
        {title}
      </h3>
      <p className="mt-2 text-gray-200 whitespace-pre-wrap leading-relaxed">{children}</p>
    </section>
  );
}

export default function TopicLearnCard({ subtopicId, onBack }) {
  const [card, setCard] = useState(null);
  const [err, setErr] = useState(null);
  const [practicing, setPracticing] = useState(false);

  useEffect(() => {
    let alive = true;
    getLearnCard(subtopicId)
      .then((c) => alive && setCard(c))
      .catch((e) =>
        alive && setErr(e?.response?.data?.detail || e?.message || "Failed to load")
      );
    return () => {
      alive = false;
    };
  }, [subtopicId]);

  if (practicing) {
    return (
      <PracticeArena
        subtopicId={subtopicId}
        subtopicName={card?.name}
        onExit={() => setPracticing(false)}
      />
    );
  }

  if (err) return <p className="text-red-400">{err}</p>;
  if (!card) return <p className="text-gray-500">Loading…</p>;

  const examples = card.examples || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="text-sm text-gray-400 hover:text-gray-200">
          ← Roadmap
        </button>
        <h2 className="text-xl font-bold text-gray-100">{card.name}</h2>
        <button
          onClick={() => setPracticing(true)}
          className="rounded-lg bg-violet-600 hover:bg-violet-500 px-4 py-2 text-sm font-medium text-white"
        >
          Practice This Subtopic →
        </button>
      </div>

      <Block title="What is it">{card.what_is_it}</Block>
      <Block title="When to use it">{card.when_to_use}</Block>
      <Block title="How to use it">{card.how_to_use}</Block>

      {examples.length > 0 && (
        <section className="rounded-xl border border-gray-800 bg-gray-900 p-5">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-violet-400">
            Worked examples
          </h3>
          <div className="mt-3 space-y-3">
            {examples.slice(0, 5).map((ex, i) => (
              <div key={i} className="rounded-lg bg-gray-950 border border-gray-800 p-4">
                <p className="text-sm font-medium text-gray-300">Example {i + 1}</p>
                <p className="mt-1 text-sm text-gray-400 whitespace-pre-wrap">{ex.prompt}</p>
                <pre className="mt-2 text-sm text-emerald-300 whitespace-pre-wrap overflow-x-auto">
                  {ex.solution}
                </pre>
              </div>
            ))}
          </div>
        </section>
      )}

      <VisualizationBlock config={card.visualization_config} />
    </div>
  );
}