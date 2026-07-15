// FILE: frontend/src/components/MLViz/TreeDepthViz.jsx
// BATCH 23 / v11 Phase 16 (new) - Drag max_depth, watch a REAL decision
// tree (CART with gini splits, implemented right here in ~50 lines) carve
// the plane into rectangles — then overfit into noise-chasing slivers.

import React, { useCallback, useMemo, useState } from "react";
import BoundaryBoard, { gaussianBlobs, mulberry32 } from "./BoundaryBoard";

// --- A tiny real CART implementation (exported for tests) ---------------
function gini(counts, total) {
  if (total === 0) return 0;
  let impurity = 1;
  Object.values(counts).forEach((c) => { impurity -= (c / total) ** 2; });
  return impurity;
}

function majority(points) {
  const counts = {};
  points.forEach((p) => { counts[p.label] = (counts[p.label] || 0) + 1; });
  return Number(Object.keys(counts)
    .reduce((a, b) => (counts[a] >= counts[b] ? a : b), 0));
}

export function buildTree(points, maxDepth, depth = 0) {
  const labels = new Set(points.map((p) => p.label));
  if (depth >= maxDepth || points.length <= 2 || labels.size === 1) {
    return { leaf: true, label: majority(points) };
  }
  let best = null;
  ["x", "y"].forEach((axis) => {
    const sorted = [...points].sort((a, b) => a[axis] - b[axis]);
    for (let i = 1; i < sorted.length; i += 1) {
      const threshold = (sorted[i - 1][axis] + sorted[i][axis]) / 2;
      const left = { counts: {}, n: 0 };
      const right = { counts: {}, n: 0 };
      points.forEach((p) => {
        const side = p[axis] <= threshold ? left : right;
        side.counts[p.label] = (side.counts[p.label] || 0) + 1;
        side.n += 1;
      });
      if (left.n === 0 || right.n === 0) continue;
      const score =
        (left.n / points.length) * gini(left.counts, left.n) +
        (right.n / points.length) * gini(right.counts, right.n);
      if (!best || score < best.score) best = { axis, threshold, score };
    }
  });
  if (!best) return { leaf: true, label: majority(points) };
  const leftPts = points.filter((p) => p[best.axis] <= best.threshold);
  const rightPts = points.filter((p) => p[best.axis] > best.threshold);
  return {
    leaf: false, axis: best.axis, threshold: best.threshold,
    left: buildTree(leftPts, maxDepth, depth + 1),
    right: buildTree(rightPts, maxDepth, depth + 1),
  };
}

export function treePredict(node, x, y) {
  while (!node.leaf) {
    const value = node.axis === "x" ? x : y;
    node = value <= node.threshold ? node.left : node.right;
  }
  return node.label;
}
// -------------------------------------------------------------------------

function noisyDataset() {
  const clean = gaussianBlobs(7, [[0.3, 0.35], [0.68, 0.66]], 34, 0.13);
  const rand = mulberry32(99);
  return clean.map((p) =>
    rand() < 0.1 ? { ...p, label: 1 - p.label } : p // 10% label noise
  );
}

export default function TreeDepthViz() {
  const [depth, setDepth] = useState(2);
  const points = useMemo(noisyDataset, []);
  const tree = useMemo(() => buildTree(points, depth), [points, depth]);
  const decide = useCallback((x, y) => treePredict(tree, x, y), [tree]);

  return (
    <div className="space-y-3">
      <BoundaryBoard points={points} decide={decide} cell={4} />
      <label className="text-sm text-gray-300 block">
        max_depth = <b className="text-cyan-400">{depth}</b>
        <input
          type="range" min="1" max="12" value={depth}
          onChange={(e) => setDepth(Number(e.target.value))}
          className="w-full accent-cyan-500"
        />
      </label>
      <p className="text-xs text-gray-500">
        <b>Interview intuition:</b> 10% of these labels are deliberately
        wrong. Depth 2-3 finds the true rectangle split; depth 10+ carves
        slivers around individual noisy points — training accuracy 100%,
        test accuracy falling. That's overfitting, and why we prune.
      </p>
    </div>
  );
}