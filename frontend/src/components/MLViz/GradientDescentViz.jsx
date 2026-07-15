// FILE: frontend/src/components/MLViz/GradientDescentViz.jsx
// BATCH 23 / v11 Phase 16 (new) - Drag the learning rate, watch gradient
// descent glide, zig-zag, or EXPLODE on a 1-D loss curve. The single best
// intuition for "why did my training diverge".

import React, { useEffect, useMemo, useRef, useState } from "react";

// Loss and its gradient (exported for tests): a valley at w = 0.6
export const loss = (w) => 2.2 * (w - 0.6) ** 2 + 0.05;
export const grad = (w) => 4.4 * (w - 0.6);

export function descentPath(w0, lr, steps) {
  const path = [w0];
  let w = w0;
  for (let i = 0; i < steps; i += 1) {
    w = w - lr * grad(w);
    if (!Number.isFinite(w) || Math.abs(w) > 50) { path.push(w); break; }
    path.push(w);
  }
  return path;
}

export default function GradientDescentViz() {
  const [lr, setLr] = useState(0.1);
  const [tick, setTick] = useState(0); // animation frame index
  const canvasRef = useRef(null);
  const path = useMemo(() => descentPath(0.05, lr, 24), [lr]);

  // restart the animation whenever the learning rate changes
  useEffect(() => { setTick(0); }, [lr]);
  useEffect(() => {
    if (tick >= path.length - 1) return undefined;
    const t = setTimeout(() => setTick((v) => v + 1), 180);
    return () => clearTimeout(t);
  }, [tick, path.length]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const width = canvas.parentElement
      ? canvas.parentElement.clientWidth : 480;
    const height = 300;
    canvas.width = width; canvas.height = height;
    const ctx = canvas.getContext("2d");
    const X = (w) => ((w + 0.4) / 2.0) * width;          // w in [-0.4, 1.6]
    const Y = (l) => height - 24 - (l / 2.6) * (height - 48);

    ctx.fillStyle = "#030712";
    ctx.fillRect(0, 0, width, height);

    // loss curve
    ctx.beginPath();
    for (let px = 0; px <= width; px += 2) {
      const w = (px / width) * 2.0 - 0.4;
      const py = Y(loss(w));
      if (px === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.strokeStyle = "#374151"; ctx.lineWidth = 2; ctx.stroke();

    // descent path up to the current tick
    const visible = path.slice(0, tick + 1);
    ctx.beginPath();
    visible.forEach((w, i) => {
      const clamped = Math.max(-0.4, Math.min(1.6, w));
      const [px, py] = [X(clamped), Y(Math.min(loss(w), 2.55))];
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    });
    ctx.strokeStyle = "#22d3ee"; ctx.lineWidth = 1.5; ctx.stroke();
    visible.forEach((w, i) => {
      const clamped = Math.max(-0.4, Math.min(1.6, w));
      ctx.beginPath();
      ctx.arc(X(clamped), Y(Math.min(loss(w), 2.55)),
              i === visible.length - 1 ? 6 : 3.5, 0, Math.PI * 2);
      ctx.fillStyle = i === visible.length - 1 ? "#f472b6" : "#22d3ee";
      ctx.fill();
    });
  }, [path, tick]);

  const diverged = Math.abs(path[path.length - 1] - 0.6) >
    Math.abs(path[0] - 0.6);

  return (
    <div className="space-y-3">
      <canvas ref={canvasRef}
        className="w-full rounded-xl border border-gray-800"
        style={{ height: 300 }} />
      <label className="text-sm text-gray-300 block">
        learning rate = <b className="text-cyan-400">{lr.toFixed(2)}</b>
        {diverged && (
          <span className="ml-2 text-red-400 font-semibold">— DIVERGED 💥</span>
        )}
        <input
          type="range" min="0.02" max="0.52" step="0.02" value={lr}
          onChange={(e) => setLr(Number(e.target.value))}
          className="w-full accent-cyan-500"
        />
      </label>
      <p className="text-xs text-gray-500">
        <b>Interview intuition:</b> below ~0.23 the ball settles into the
        valley; around 0.35 it zig-zags across it; past ~0.45 each step
        overshoots MORE than the last — divergence. Learning rate is the
        most important hyperparameter you'll ever tune.
      </p>
    </div>
  );
}