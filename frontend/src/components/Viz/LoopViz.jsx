// frontend/src/components/Viz/LoopViz.jsx
/**
 * ATLAS AI 4.0 - v12 viz pack: loop_viz (Python topic).
 * Step through `for x in items:` one iteration at a time - the loop
 * variable, the highlighted element, and the accumulating output are all
 * visible at once. Dependency-free SVG + state.
 */

import { useState } from "react";

const ITEMS = [3, 8, 1, 5, 9];

export default function LoopViz() {
  const [i, setI] = useState(-1); // -1 = not started
  const done = i >= ITEMS.length - 1;
  const outputs = ITEMS.slice(0, Math.max(0, i + 1)).map((v) => v * 2);

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
      <pre className="mb-2 font-mono text-xs text-sky-200">
{`total = []
for x in items:      ${i >= 0 && !done ? `# x = ${ITEMS[i]}` : ""}
    total.append(x * 2)`}
      </pre>

      <svg viewBox="0 0 300 70" className="w-full">
        {ITEMS.map((v, idx) => (
          <g key={idx}>
            <rect x={10 + idx * 56} y={18} width={46} height={30} rx={6}
                  fill={idx === i ? "#0ea5e9" : idx < i ? "#134e4a" : "#27272a"}
                  stroke={idx === i ? "#7dd3fc" : "#3f3f46"} />
            <text x={33 + idx * 56} y={38} textAnchor="middle"
                  fill="#e4e4e7" fontSize="13">{v}</text>
            <text x={33 + idx * 56} y={62} textAnchor="middle"
                  fill="#71717a" fontSize="9">items[{idx}]</text>
          </g>
        ))}
        {i >= 0 && i < ITEMS.length && (
          <text x={33 + i * 56} y={12} textAnchor="middle"
                fill="#7dd3fc" fontSize="10">x</text>
        )}
      </svg>

      <p className="mt-1 font-mono text-xs text-zinc-400">
        total = [{outputs.join(", ")}]
      </p>

      <div className="mt-2 flex gap-2">
        <button type="button"
          onClick={() => setI((n) => Math.min(n + 1, ITEMS.length - 1))}
          disabled={done}
          className="rounded bg-sky-700 px-3 py-1 text-xs text-white
                     hover:bg-sky-600 disabled:bg-zinc-700">
          {i < 0 ? "Start loop" : "Next iteration →"}
        </button>
        <button type="button" onClick={() => setI(-1)}
          className="rounded border border-zinc-700 px-3 py-1 text-xs text-zinc-300">
          Reset
        </button>
        {done && <span className="text-xs text-emerald-400 self-center">loop finished ✓</span>}
      </div>
    </div>
  );
}