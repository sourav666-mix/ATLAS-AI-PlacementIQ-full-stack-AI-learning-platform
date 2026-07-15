// frontend/src/components/Viz/DistributionViz.jsx
/**
 * ATLAS AI 4.0 - v12 viz pack: distribution_viz (Stats topic).
 * A live normal curve: drag mean and std-dev and see the bell move,
 * widen and flatten - plus the shaded ±1σ region (~68%).
 * Doubles as chart_viz fallback for Data Visualization.
 */

import { useState } from "react";

function normalPath(mu, sigma, W, H) {
  const pts = [];
  for (let px = 0; px <= W; px += 4) {
    const x = (px / W) * 10; // domain 0..10
    const y = Math.exp(-((x - mu) ** 2) / (2 * sigma ** 2)) / (sigma * Math.sqrt(2 * Math.PI));
    pts.push([px, H - 8 - y * H * 2.1]);
  }
  return pts;
}

export default function DistributionViz() {
  const [mu, setMu] = useState(5);
  const [sigma, setSigma] = useState(1);
  const W = 320, H = 120;
  const pts = normalPath(mu, sigma, W, H);
  const line = pts.map(([x, y], i) => `${i ? "L" : "M"}${x},${y.toFixed(1)}`).join(" ");
  const x1 = ((mu - sigma) / 10) * W, x2 = ((mu + sigma) / 10) * W;
  const band = pts.filter(([x]) => x >= x1 && x <= x2);
  const area = band.length
    ? `M${x1},${H - 8} ` + band.map(([x, y]) => `L${x},${y.toFixed(1)}`).join(" ") + ` L${x2},${H - 8} Z`
    : "";

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
      <p className="mb-1 font-mono text-xs text-sky-200">
        X ~ N(μ={mu.toFixed(1)}, σ={sigma.toFixed(1)}) · shaded ±1σ ≈ 68%
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
        <line x1="0" y1={H - 8} x2={W} y2={H - 8} stroke="#3f3f46" />
        {area && <path d={area} fill="#0ea5e955" />}
        <path d={line} fill="none" stroke="#38bdf8" strokeWidth="2" />
        <line x1={(mu / 10) * W} y1={10} x2={(mu / 10) * W} y2={H - 8}
              stroke="#f59e0b" strokeDasharray="3 3" />
      </svg>
      <div className="mt-1 space-y-1 text-xs text-zinc-400">
        <label className="flex items-center gap-2">
          <span className="w-8">μ={mu.toFixed(1)}</span>
          <input type="range" min="2" max="8" step="0.1" value={mu}
                 onChange={(e) => setMu(Number(e.target.value))}
                 className="flex-1 accent-sky-500" />
        </label>
        <label className="flex items-center gap-2">
          <span className="w-8">σ={sigma.toFixed(1)}</span>
          <input type="range" min="0.4" max="2.5" step="0.1" value={sigma}
                 onChange={(e) => setSigma(Number(e.target.value))}
                 className="flex-1 accent-sky-500" />
        </label>
      </div>
    </div>
  );
}