// frontend/src/components/Viz/NetworkViz.jsx
/**
 * ATLAS AI 4.0 - v12 viz pack: network_viz (Deep Learning topic).
 * A 3-4-2 network animating a forward pass layer by layer - activations
 * light up, edge thickness = weight magnitude. Click "Forward pass" to
 * sweep; deterministic toy weights so the story is repeatable.
 */

import { useState } from "react";

const LAYERS = [3, 4, 2];
const XS = [40, 160, 280];
const nodeY = (count, i) => 20 + i * (100 / Math.max(count - 1, 1));
// deterministic pseudo-weights in [-1, 1]
const w = (l, i, j) => Math.sin(l * 7 + i * 3 + j * 5);

export default function NetworkViz() {
  const [stage, setStage] = useState(0); // 0 idle, 1 hidden lit, 2 output lit

  const advance = () => setStage((s) => (s >= 2 ? 0 : s + 1));

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
      <p className="mb-1 font-mono text-xs text-sky-200">
        h = σ(W₁x)  →  ŷ = σ(W₂h)
        <span className="ml-2 text-zinc-500">
          {stage === 0 ? "input ready" : stage === 1 ? "hidden layer computed" : "output computed"}
        </span>
      </p>
      <svg viewBox="0 0 320 140" className="w-full">
        {/* edges */}
        {LAYERS.slice(0, -1).map((n, l) =>
          Array.from({ length: n }).map((_, i) =>
            Array.from({ length: LAYERS[l + 1] }).map((_, j) => (
              <line key={`${l}-${i}-${j}`}
                    x1={XS[l]} y1={nodeY(n, i) + 10}
                    x2={XS[l + 1]} y2={nodeY(LAYERS[l + 1], j) + 10}
                    stroke={stage > l ? (w(l, i, j) > 0 ? "#38bdf8" : "#f472b6") : "#3f3f46"}
                    strokeWidth={0.6 + Math.abs(w(l, i, j)) * 2}
                    opacity={stage > l ? 0.9 : 0.4} />
            ))))}
        {/* nodes */}
        {LAYERS.map((n, l) =>
          Array.from({ length: n }).map((_, i) => (
            <circle key={`n${l}-${i}`} cx={XS[l]} cy={nodeY(n, i) + 10} r={9}
                    fill={stage >= l ? "#0ea5e9" : "#27272a"}
                    stroke={stage >= l ? "#7dd3fc" : "#3f3f46"} />
          )))}
        <text x={XS[0]} y={135} textAnchor="middle" fill="#71717a" fontSize="9">input x</text>
        <text x={XS[1]} y={135} textAnchor="middle" fill="#71717a" fontSize="9">hidden h</text>
        <text x={XS[2]} y={135} textAnchor="middle" fill="#71717a" fontSize="9">output ŷ</text>
      </svg>
      <div className="mt-1 flex items-center gap-2">
        <button type="button" onClick={advance}
          className="rounded bg-sky-700 px-3 py-1 text-xs text-white hover:bg-sky-600">
          {stage >= 2 ? "Reset" : "Forward pass →"}
        </button>
        <span className="text-[11px] text-zinc-500">
          blue edges = positive weights, pink = negative; thickness = |w|
        </span>
      </div>
    </div>
  );
}