// FILE: frontend/src/components/MLViz/KNNExplorer.jsx
// BATCH 23 / v11 Phase 16 (new) - Drag k, watch the KNN boundary change.
// k=1 memorises every point (jagged islands = overfitting); large k smooths
// toward the majority class (underfitting). Click the board to add points
// of the selected class and watch the boundary react instantly.

import React, { useCallback, useMemo, useState } from "react";
import BoundaryBoard, { CLASS_COLORS, gaussianBlobs } from "./BoundaryBoard";

// Pure kNN vote — exported for tests
export function knnClassify(points, x, y, k) {
  const nearest = points
    .map((p) => ({ label: p.label, d: (p.x - x) ** 2 + (p.y - y) ** 2 }))
    .sort((a, b) => a.d - b.d)
    .slice(0, Math.max(1, Math.min(k, points.length)));
  const votes = {};
  nearest.forEach((n) => { votes[n.label] = (votes[n.label] || 0) + 1; });
  return Number(
    Object.keys(votes).reduce((a, b) => (votes[a] >= votes[b] ? a : b))
  );
}

export default function KNNExplorer() {
  const [k, setK] = useState(3);
  const [brush, setBrush] = useState(0);
  const [points, setPoints] = useState(() =>
    gaussianBlobs(42, [[0.32, 0.62], [0.68, 0.38]], 30, 0.11)
  );

  const decide = useCallback(
    (x, y) => knnClassify(points, x, y, k),
    [points, k]
  );
  const addPoint = useCallback(
    (x, y) => setPoints((prev) => [...prev, { x, y, label: brush }]),
    [brush]
  );
  const board = useMemo(
    () => (
      <BoundaryBoard points={points} decide={decide} onAddPoint={addPoint} />
    ),
    [points, decide, addPoint]
  );

  return (
    <div className="space-y-3">
      {board}
      <div className="flex items-center gap-4">
        <label className="text-sm text-gray-300 flex-1">
          k = <b className="text-cyan-400">{k}</b>
          <input
            type="range" min="1" max="19" step="2" value={k}
            onChange={(e) => setK(Number(e.target.value))}
            className="w-full accent-cyan-500"
          />
        </label>
        <div className="flex gap-1">
          {[0, 1].map((cls) => (
            <button
              key={cls}
              onClick={() => setBrush(cls)}
              className={`px-3 py-1.5 rounded-lg text-xs border ${
                brush === cls ? "border-white" : "border-gray-700"
              }`}
              style={{ color: CLASS_COLORS[cls] }}
            >
              add class {cls}
            </button>
          ))}
        </div>
      </div>
      <p className="text-xs text-gray-500">
        <b>Interview intuition:</b> k=1 → high variance (memorising noise);
        big k → high bias (ignoring structure). The sweet spot balances both
        — that's the bias-variance tradeoff, live.
      </p>
    </div>
  );
}