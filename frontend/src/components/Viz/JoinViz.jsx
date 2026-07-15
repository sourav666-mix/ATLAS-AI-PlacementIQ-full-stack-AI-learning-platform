// frontend/src/components/Viz/JoinViz.jsx
/**
 * ATLAS AI 4.0 - v12 viz pack: join_viz (SQL / Pandas merge topic).
 * Two tiny tables, four join types. Switch INNER/LEFT/RIGHT/OUTER and
 * watch which rows survive and where the NULLs appear - the whole join
 * mental model in one picture. Dependency-free, pure React state.
 */

import { useState } from "react";

const STUDENTS = [
  { name: "Asha", branch: "CSE" },
  { name: "Rahul", branch: "ECE" },
  { name: "Meera", branch: "CSE" },
  { name: "Vikram", branch: "ME" },
];

const OFFERS = [
  { name: "Asha", company: "TCS" },
  { name: "Meera", company: "Infosys" },
  { name: "Divya", company: "Wipro" },
];

const HOW = ["inner", "left", "right", "outer"];

function joinRows(how) {
  const offerNames = new Set(OFFERS.map((o) => o.name));
  const studentNames = new Set(STUDENTS.map((s) => s.name));
  const rows = [];

  STUDENTS.forEach((s) => {
    const match = OFFERS.find((o) => o.name === s.name);
    if (match) rows.push({ name: s.name, branch: s.branch, company: match.company });
    else if (how === "left" || how === "outer")
      rows.push({ name: s.name, branch: s.branch, company: null });
  });
  if (how === "right" || how === "outer") {
    OFFERS.filter((o) => !studentNames.has(o.name)).forEach((o) =>
      rows.push({ name: o.name, branch: null, company: o.company })
    );
  }
  return { rows, offerNames, studentNames };
}

function Null() {
  return <span className="italic text-amber-600">NULL</span>;
}

export default function JoinViz() {
  const [how, setHow] = useState("inner");
  const { rows, offerNames, studentNames } = joinRows(how);

  const keyClass = (matched) => (matched ? "text-sky-300" : "text-zinc-500");

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-xs">
      <p className="mb-2 font-mono text-sky-200">
        pd.merge(students, offers, on="name", how="{how}")
      </p>

      <div className="mb-2 grid grid-cols-2 gap-3">
        <table className="text-left">
          <thead><tr className="text-zinc-500">
            <th className="py-1" colSpan={2}>students</th></tr></thead>
          <tbody>
            {STUDENTS.map((s) => (
              <tr key={s.name} className="text-zinc-300">
                <td className={`py-0.5 pr-2 ${keyClass(offerNames.has(s.name))}`}>{s.name}</td>
                <td>{s.branch}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <table className="text-left">
          <thead><tr className="text-zinc-500">
            <th className="py-1" colSpan={2}>offers</th></tr></thead>
          <tbody>
            {OFFERS.map((o) => (
              <tr key={o.name} className="text-zinc-300">
                <td className={`py-0.5 pr-2 ${keyClass(studentNames.has(o.name))}`}>{o.name}</td>
                <td>{o.company}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <table className="w-full text-left">
        <thead><tr className="text-zinc-500">
          <th className="py-1">name</th><th>branch</th><th>company</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.name} className="text-zinc-200">
              <td className="py-0.5">{r.name}</td>
              <td>{r.branch ?? <Null />}</td>
              <td>{r.company ?? <Null />}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-1 text-zinc-500">
        {rows.length} row{rows.length === 1 ? "" : "s"} — keys in{" "}
        <span className="text-sky-300">blue</span> exist in both tables.
      </p>

      <div className="mt-2 flex gap-2">
        {HOW.map((h) => (
          <button key={h} type="button" onClick={() => setHow(h)}
            className={`rounded px-3 py-1 uppercase text-white
                        ${how === h ? "bg-sky-700" : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"}`}>
            {h}
          </button>
        ))}
      </div>
    </div>
  );
}
