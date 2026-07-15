// frontend/src/components/Viz/GradientDescentViz.jsx
/**
 * ATLAS AI 4.0 - v12 viz pack: gradient_descent_viz (Machine Learning).
 * The ball rolls down the loss bowl one step at a time; the learning
 * rate slider makes it crawl, converge, or OVERSHOOT and diverge - the
 * exact intuition every ML interview probes.
 * Doubles as loss_curve_viz for Fine-Tuning.
 */

import { useState } from "react";

const f = (x) => 0.25 * x * x;         // loss bowl
const grad = (x) => 0.5 * x;           // its derivative
const W = 320, H = 130, X0 = 8;

const toPx = (x) => ((x + 10) / 20) * W;
const toPy = (y) => H - 12 - y * 3.6;

export default function GradientDescentViz() {
  const [lr, setLr] = useState(1.0);
  const [xs, setXs] = useState([X0]);
  const x = xs[xs.length - 1];
  const diverged = Math.abs(x) > 20;

  const stepOnce = () =>
    setXs((h) => (Math.abs(h[h.length - 1]) > 20 ? h
      : [...h, h[h.length - 1] - lr * grad(h[h.length - 1])]));
  const reset = () => setXs([X0]);

  const curve = [];
  for (let px = 0; px <= W; px += 4) {
    const xv = (px / W) * 20 - 10;
    curve.push(`${px ? "L" : "M"}${px},${toPy(f(xv)).toFixed(1)}`);
  }

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
      <p className="mb-1 font-mono text-xs text-sky-200">
        x ← x − η·∇L(x) · η={lr.toFixed(2)} · step {xs.length - 1} · x={x.toFixed(2)}
        {diverged && <span className="text-red-400">  DIVERGED — η too big!</span>}
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
        <path d={curve.join(" ")} fill="none" stroke="#38bdf8" strokeWidth="2" />
        {xs.slice(-12).map((xv, i, arr) => (
          <circle key={i} cx={toPx(Math.max(-10, Math.min(10, xv)))}
                  cy={toPy(f(Math.max(-10, Math.min(10, xv))))}
                  r={i === arr.length - 1 ? 6 : 3}
                  fill={i === arr.length - 1 ? "#f59e0b" : "#f59e0b66"} />
        ))}
        <text x={toPx(0)} y={H - 1} textAnchor="middle" fill="#71717a" fontSize="9">
          minimum
        </text>
      </svg>
      <div className="mt-1 flex items-center gap-2 text-xs text-zinc-400">
        <span>η={lr.toFixed(2)}</span>
        <input type="range" min="0.1" max="5.0" step="0.1" value={lr}
               onChange={(e) => setLr(Number(e.target.value))}
               className="flex-1 accent-sky-500" />
        <button type="button" onClick={stepOnce}
          className="rounded bg-sky-700 px-3 py-1 text-white hover:bg-sky-600">
          Step
        </button>
        <button type="button" onClick={reset}
          className="rounded border border-zinc-700 px-2 py-1 text-zinc-300">
          Reset
        </button>
      </div>
    </div>
  );
}