// FILE: frontend/src/components/MLViz/ClusterViz.jsx
// BATCH 23 / v11 Phase 16 (new) - Real k-means, one iteration per click:
// ASSIGN points to their nearest centroid, then MOVE each centroid to the
// mean of its points. Watch the centroids walk into the blobs — or fight
// over one blob when k is wrong.

import React, { useCallback, useMemo, useState } from "react";
import BoundaryBoard, { CLASS_COLORS, gaussianBlobs, mulberry32 }
  from "./BoundaryBoard";

// One k-means iteration (exported for tests):
// returns {centroids, assignments, moved}
export function kmeansStep(points, centroids) {
  const assignments = points.map((p) => {
    let best = 0; let bestD = Infinity;
    centroids.forEach((c, i) => {
      const d = (p.x - c.x) ** 2 + (p.y - c.y) ** 2;
      if (d < bestD) { bestD = d; best = i; }
    });
    return best;
  });
  let moved = 0;
  const next = centroids.map((c, i) => {
    const mine = points.filter((_, idx) => assignments[idx] === i);
    if (mine.length === 0) return c;
    const nx = mine.reduce((s, p) => s + p.x, 0) / mine.length;
    const ny = mine.reduce((s, p) => s + p.y, 0) / mine.length;
    moved += Math.abs(nx - c.x) + Math.abs(ny - c.y);
    return { x: nx, y: ny };
  });
  return { centroids: next, assignments, moved };
}

function randomCentroids(k, seed) {
  const rand = mulberry32(seed);
  return Array.from({ length: k }, () => ({ x: rand(), y: rand() }));
}

const DATA = () =>
  gaussianBlobs(11, [[0.25, 0.7], [0.7, 0.65], [0.5, 0.25]], 26, 0.075)
    .map((p) => ({ ...p, label: 0 })); // labels hidden — it's unsupervised!

export default function ClusterViz() {
  const [k, setK] = useState(3);
  const points = useMemo(DATA, []);
  const [state, setState] = useState(() => ({
    centroids: randomCentroids(3, 5),
    assignments: points.map(() => 0),
    iterations: 0,
    converged: false,
  }));

  const reset = useCallback((newK) => {
    setK(newK);
    setState({
      centroids: randomCentroids(newK, 5 + newK),
      assignments: points.map(() => 0),
      iterations: 0,
      converged: false,
    });
  }, [points]);

  const step = useCallback(() => {
    setState((prev) => {
      const { centroids, assignments, moved } =
        kmeansStep(points, prev.centroids);
      return {
        centroids, assignments,
        iterations: prev.iterations + 1,
        converged: moved < 1e-4,
      };
    });
  }, [points]);

  const colored = points.map((p, i) => ({
    ...p, label: state.assignments[i],
  }));

  const drawCentroids = useCallback((ctx, toPx) => {
    state.centroids.forEach((c, i) => {
      const [px, py] = toPx(c.x, c.y);
      ctx.strokeStyle = CLASS_COLORS[i % CLASS_COLORS.length];
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(px - 7, py - 7); ctx.lineTo(px + 7, py + 7);
      ctx.moveTo(px + 7, py - 7); ctx.lineTo(px - 7, py + 7);
      ctx.stroke();
    });
  }, [state.centroids]);

  return (
    <div className="space-y-3">
      <BoundaryBoard points={colored} extraDraw={drawCentroids} />
      <div className="flex items-center gap-3">
        <label className="text-sm text-gray-300 flex-1">
          k = <b className="text-cyan-400">{k}</b>
          <input
            type="range" min="2" max="6" value={k}
            onChange={(e) => reset(Number(e.target.value))}
            className="w-full accent-cyan-500"
          />
        </label>
        <button
          onClick={step}
          disabled={state.converged}
          className="px-4 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white font-medium"
        >
          {state.converged
            ? `Converged in ${state.iterations}`
            : `Step (${state.iterations})`}
        </button>
        <button
          onClick={() => reset(k)}
          className="px-3 py-2 text-sm rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300"
        >
          reset
        </button>
      </div>
      <p className="text-xs text-gray-500">
        <b>Interview intuition:</b> the data has 3 natural blobs. Set k=3 and
        centroids settle in ~4 steps; k=2 forces two blobs to share; k=5
        splits a real cluster. k-means always converges — but only to a
        LOCAL optimum, which is why we run it with multiple inits.
      </p>
    </div>
  );
}