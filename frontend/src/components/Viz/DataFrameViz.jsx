// frontend/src/components/Viz/DataFrameViz.jsx
/**
 * ATLAS AI 4.0 - v12 viz pack: dataframe_viz (Pandas topic).
 * Toggle a filter and a groupby on a tiny placements DataFrame and watch
 * rows drop out / collapse into groups - selection, filtering and
 * aggregation in one picture.
 */

import { useState } from "react";

const ROWS = [
  { name: "Asha", branch: "CSE", cgpa: 8.9 },
  { name: "Rahul", branch: "ECE", cgpa: 7.4 },
  { name: "Meera", branch: "CSE", cgpa: 9.2 },
  { name: "Vikram", branch: "ME", cgpa: 6.8 },
  { name: "Divya", branch: "ECE", cgpa: 8.1 },
];

export default function DataFrameViz() {
  const [minCgpa, setMinCgpa] = useState(0);
  const [grouped, setGrouped] = useState(false);

  const filtered = ROWS.filter((r) => r.cgpa >= minCgpa);
  const groups = {};
  filtered.forEach((r) => {
    groups[r.branch] = groups[r.branch] || [];
    groups[r.branch].push(r.cgpa);
  });

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-xs">
      <p className="mb-2 font-mono text-sky-200">
        df[df.cgpa &gt;= {minCgpa.toFixed(1)}]{grouped ? ".groupby('branch').cgpa.mean()" : ""}
      </p>

      {!grouped ? (
        <table className="w-full text-left">
          <thead><tr className="text-zinc-500">
            <th className="py-1">name</th><th>branch</th><th>cgpa</th></tr></thead>
          <tbody>
            {ROWS.map((r) => (
              <tr key={r.name}
                  className={filtered.includes(r)
                    ? "text-zinc-200" : "text-zinc-700 line-through"}>
                <td className="py-1">{r.name}</td><td>{r.branch}</td><td>{r.cgpa}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <table className="w-full text-left">
          <thead><tr className="text-zinc-500">
            <th className="py-1">branch</th><th>mean(cgpa)</th><th>rows</th></tr></thead>
          <tbody>
            {Object.entries(groups).map(([b, vals]) => (
              <tr key={b} className="text-zinc-200">
                <td className="py-1">{b}</td>
                <td>{(vals.reduce((a, c) => a + c, 0) / vals.length).toFixed(2)}</td>
                <td className="text-zinc-500">{vals.length}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="mt-2 flex items-center gap-3">
        <label className="flex flex-1 items-center gap-2 text-zinc-400">
          min cgpa {minCgpa.toFixed(1)}
          <input type="range" min="0" max="9" step="0.5" value={minCgpa}
                 onChange={(e) => setMinCgpa(Number(e.target.value))}
                 className="flex-1 accent-sky-500" />
        </label>
        <button type="button" onClick={() => setGrouped((g) => !g)}
          className={`rounded px-3 py-1 text-white
                      ${grouped ? "bg-emerald-700" : "bg-sky-700"}`}>
          {grouped ? "ungroup" : "groupby(branch)"}
        </button>
      </div>
    </div>
  );
}