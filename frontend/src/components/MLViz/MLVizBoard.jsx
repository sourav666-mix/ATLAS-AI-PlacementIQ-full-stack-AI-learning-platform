// FILE: frontend/src/components/MLViz/MLVizBoard.jsx
// BATCH 23 / v11 Phase 16 (new) - The gallery: four interactive intuition
// widgets behind tabs. Mounted as its own route (/ml-viz) AND embeddable
// inside the AI/ML Live Lab. Everything here is client-side canvas math.

import React, { useState } from "react";
import KNNExplorer from "./KNNExplorer";
import TreeDepthViz from "./TreeDepthViz";
import GradientDescentViz from "./GradientDescentViz";
import ClusterViz from "./ClusterViz";

const TABS = [
  { id: "knn", label: "KNN boundary", component: KNNExplorer,
    blurb: "Drag k — watch overfitting become underfitting" },
  { id: "tree", label: "Tree depth", component: TreeDepthViz,
    blurb: "A real decision tree carving the plane" },
  { id: "gd", label: "Gradient descent", component: GradientDescentViz,
    blurb: "Drag the learning rate — make it diverge" },
  { id: "kmeans", label: "k-means", component: ClusterViz,
    blurb: "Step the centroids into the blobs" },
];

export default function MLVizBoard({ embedded = false }) {
  const [active, setActive] = useState("knn");
  const tab = TABS.find((t) => t.id === active) || TABS[0];
  const Active = tab.component;

  const body = (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setActive(t.id)}
            className={`px-3 py-1.5 text-xs rounded-lg border transition ${
              active === t.id
                ? "border-cyan-600 bg-cyan-950/40 text-cyan-300"
                : "border-gray-800 bg-gray-900 text-gray-400 hover:border-gray-600"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <p className="text-sm text-gray-400">{tab.blurb}</p>
      <Active />
    </div>
  );

  if (embedded) return body;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-4 lg:p-6">
      <div className="max-w-3xl mx-auto space-y-4">
        <div>
          <h1 className="text-2xl font-bold">ML Intuition Board</h1>
          <p className="text-sm text-gray-400">
            The concepts interviewers actually probe — made draggable.
            Runs entirely on your machine.
          </p>
        </div>
        {body}
      </div>
    </div>
  );
}