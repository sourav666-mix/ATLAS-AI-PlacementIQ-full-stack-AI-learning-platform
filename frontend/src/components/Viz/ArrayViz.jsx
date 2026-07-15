// frontend/src/components/Viz/ArrayViz.jsx
/**
 * ATLAS AI 4.0 - v12 viz pack: array_viz (NumPy topic).
 * Live slicing: drag start/stop/step and watch a[start:stop:step] light
 * up - the single most confusing NumPy idea made tactile.
 */

import { useState } from "react";

const A = [10, 11, 12, 13, 14, 15, 16, 17];

export default function ArrayViz() {
  const [start, setStart] = useState(1);
  const [stop, setStop] = useState(6);
  const [step, setStep] = useState(2);

  const picked = new Set();
  for (let i = start; i < stop; i += step) if (i >= 0 && i < A.length) picked.add(i);

  const Slider = ({ label, value, set, min, max }) => (
    <label className="flex items-center gap-2 text-xs text-zinc-400">
      <span className="w-10">{label}={value}</span>
      <input type="range" min={min} max={max} value={value}
             onChange={(e) => set(Number(e.target.value))}
             className="flex-1 accent-sky-500" />
    </label>
  );

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
      <p className="mb-2 font-mono text-xs text-sky-200">
        a[{start}:{stop}:{step}]  →  [{[...picked].map((i) => A[i]).join(", ")}]
      </p>
      <svg viewBox="0 0 340 60" className="w-full">
        {A.map((v, idx) => (
          <g key={idx}>
            <rect x={6 + idx * 41} y={12} width={35} height={28} rx={5}
                  fill={picked.has(idx) ? "#0ea5e9" : "#27272a"}
                  stroke={picked.has(idx) ? "#7dd3fc" : "#3f3f46"} />
            <text x={23 + idx * 41} y={31} textAnchor="middle"
                  fill="#e4e4e7" fontSize="12">{v}</text>
            <text x={23 + idx * 41} y={54} textAnchor="middle"
                  fill="#71717a" fontSize="9">{idx}</text>
          </g>
        ))}
      </svg>
      <div className="mt-2 space-y-1">
        <Slider label="start" value={start} set={setStart} min={0} max={7} />
        <Slider label="stop" value={stop} set={setStop} min={0} max={8} />
        <Slider label="step" value={step} set={setStep} min={1} max={3} />
      </div>
    </div>
  );
}