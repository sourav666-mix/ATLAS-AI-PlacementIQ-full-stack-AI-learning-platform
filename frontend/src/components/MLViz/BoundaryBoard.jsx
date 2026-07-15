// FILE: frontend/src/components/MLViz/BoundaryBoard.jsx
// BATCH 23 / v11 Phase 16 (new) - The SHARED base for every ML intuition
// widget: a canvas that (1) paints a decision region by evaluating a
// decide(x,y) function over a coarse grid, (2) draws the data points on
// top, (3) lets the student click to add points. 100% client-side math —
// zero backend, zero AI, zero cost. x/y are in [0,1] data space.

import React, { useEffect, useRef } from "react";

export const CLASS_COLORS = ["#22d3ee", "#f472b6", "#a3e635", "#fbbf24"];
export const REGION_COLORS = ["#164e63", "#500724", "#365314", "#451a03"];

// Deterministic RNG so every student sees the same starter dataset
export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function gaussianBlobs(seed, centers, perClass, spread) {
  const rand = mulberry32(seed);
  const gauss = () =>
    Math.sqrt(-2 * Math.log(rand() + 1e-9)) * Math.cos(2 * Math.PI * rand());
  const points = [];
  centers.forEach(([cx, cy], label) => {
    for (let i = 0; i < perClass; i += 1) {
      points.push({
        x: Math.min(0.98, Math.max(0.02, cx + gauss() * spread)),
        y: Math.min(0.98, Math.max(0.02, cy + gauss() * spread)),
        label,
      });
    }
  });
  return points;
}

export default function BoundaryBoard({
  points = [],
  decide = null,          // (x, y) -> class index, or null for no regions
  extraDraw = null,       // (ctx, toPx) -> custom overlay (paths, centroids)
  onAddPoint = null,      // (x, y) in data space
  height = 320,
  cell = 6,               // px per region cell (bigger = faster)
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const width = canvas.parentElement
      ? canvas.parentElement.clientWidth
      : 480;
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    const toPx = (x, y) => [x * width, (1 - y) * height];

    // background
    ctx.fillStyle = "#030712";
    ctx.fillRect(0, 0, width, height);

    // decision regions
    if (decide) {
      for (let px = 0; px < width; px += cell) {
        for (let py = 0; py < height; py += cell) {
          const x = (px + cell / 2) / width;
          const y = 1 - (py + cell / 2) / height;
          const cls = decide(x, y);
          ctx.fillStyle = REGION_COLORS[cls % REGION_COLORS.length];
          ctx.fillRect(px, py, cell, cell);
        }
      }
    }

    // points
    points.forEach((p) => {
      const [px, py] = toPx(p.x, p.y);
      ctx.beginPath();
      ctx.arc(px, py, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = CLASS_COLORS[p.label % CLASS_COLORS.length];
      ctx.fill();
      ctx.strokeStyle = "#030712";
      ctx.lineWidth = 1.5;
      ctx.stroke();
    });

    if (extraDraw) extraDraw(ctx, toPx);
  }, [points, decide, extraDraw, height, cell]);

  const handleClick = (event) => {
    if (!onAddPoint) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const y = 1 - (event.clientY - rect.top) / rect.height;
    onAddPoint(Math.min(0.99, Math.max(0.01, x)),
               Math.min(0.99, Math.max(0.01, y)));
  };

  return (
    <canvas
      ref={canvasRef}
      onClick={handleClick}
      className={`w-full rounded-xl border border-gray-800 ${
        onAddPoint ? "cursor-crosshair" : ""
      }`}
      style={{ height }}
    />
  );
}