// BuilderForm.jsx - [NEW] guided resume form
// FILE: frontend/src/components/Resume/BuilderForm.jsx
// BATCH 29 / v10 Resume AI (new) - The guided builder form (Mode B). Required
// core fields + optional extras; repeatable education / projects / experience
// rows. Submits raw inputs to /resume/builder/draft for AI drafting.

import React, { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button, Spinner } from "../Common";

const emptyEdu = { degree: "", institution: "", year: "", score: "" };
const emptyProj = { name: "", tech: "", description: "" };
const emptyExp = { role: "", company: "", duration: "", details: "" };

function Field({ label, value, onChange, placeholder, type = "text", required }) {
  return (
    <label className="block">
      <span className="text-xs text-gray-400">
        {label}{required && <span className="text-red-400"> *</span>}
      </span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1 w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-cyan-700"
      />
    </label>
  );
}

export default function BuilderForm({ onDraft, drafting }) {
  const [f, setF] = useState({
    full_name: "", phone: "", email: "", address: "", specialization: "",
    skills: "", linkedin: "", github: "", job_description: "",
    education: [{ ...emptyEdu }],
    projects: [{ ...emptyProj }],
    experience: [],
  });
  const [error, setError] = useState(null);

  const set = (k) => (v) => setF((prev) => ({ ...prev, [k]: v }));
  const setRow = (list, i, key, v) =>
    setF((prev) => {
      const arr = [...prev[list]];
      arr[i] = { ...arr[i], [key]: v };
      return { ...prev, [list]: arr };
    });
  const addRow = (list, blank) =>
    setF((prev) => ({ ...prev, [list]: [...prev[list], { ...blank }] }));
  const removeRow = (list, i) =>
    setF((prev) => ({ ...prev, [list]: prev[list].filter((_, idx) => idx !== i) }));

  const submit = () => {
    setError(null);
    if (!f.full_name || !f.email || !f.specialization) {
      setError("Name, email, and specialization are required.");
      return;
    }
    onDraft({
      ...f,
      skills: f.skills.split(",").map((s) => s.trim()).filter(Boolean),
    });
  };

  return (
    <div className="space-y-6">
      <section className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3">
        <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Basics</p>
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label="Full name" value={f.full_name} onChange={set("full_name")} required />
          <Field label="Email" type="email" value={f.email} onChange={set("email")} required />
          <Field label="Phone" value={f.phone} onChange={set("phone")} />
          <Field label="Location" value={f.address} onChange={set("address")} placeholder="City, State" />
          <Field label="Specialization" value={f.specialization} onChange={set("specialization")} placeholder="e.g. Data Science" required />
          <Field label="Skills (comma-separated)" value={f.skills} onChange={set("skills")} placeholder="Python, SQL, Pandas" />
          <Field label="LinkedIn (optional)" value={f.linkedin} onChange={set("linkedin")} />
          <Field label="GitHub (optional)" value={f.github} onChange={set("github")} />
        </div>
      </section>

      {/* Education */}
      <section className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Education</p>
          <button onClick={() => addRow("education", emptyEdu)} className="text-cyan-400 hover:text-cyan-300 text-xs flex items-center gap-1">
            <Plus size={13} /> Add
          </button>
        </div>
        {f.education.map((row, i) => (
          <div key={i} className="grid sm:grid-cols-4 gap-2 items-end">
            <Field label="Degree" value={row.degree} onChange={(v) => setRow("education", i, "degree", v)} />
            <Field label="Institution" value={row.institution} onChange={(v) => setRow("education", i, "institution", v)} />
            <Field label="Year" value={row.year} onChange={(v) => setRow("education", i, "year", v)} />
            <div className="flex gap-1">
              <Field label="Score" value={row.score} onChange={(v) => setRow("education", i, "score", v)} />
              {f.education.length > 1 && (
                <button onClick={() => removeRow("education", i)} className="text-red-400 hover:text-red-300 pb-2">
                  <Trash2 size={15} />
                </button>
              )}
            </div>
          </div>
        ))}
      </section>

      {/* Projects */}
      <section className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Projects</p>
          <button onClick={() => addRow("projects", emptyProj)} className="text-cyan-400 hover:text-cyan-300 text-xs flex items-center gap-1">
            <Plus size={13} /> Add
          </button>
        </div>
        {f.projects.map((row, i) => (
          <div key={i} className="space-y-2 rounded-xl bg-gray-950 border border-gray-800 p-3">
            <div className="grid sm:grid-cols-2 gap-2">
              <Field label="Project name" value={row.name} onChange={(v) => setRow("projects", i, "name", v)} />
              <Field label="Tech used" value={row.tech} onChange={(v) => setRow("projects", i, "tech", v)} />
            </div>
            <label className="block">
              <span className="text-xs text-gray-400">What you did (plain words — AI rewrites to STAR)</span>
              <textarea
                value={row.description}
                onChange={(e) => setRow("projects", i, "description", e.target.value)}
                rows={2}
                className="mt-1 w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-cyan-700"
              />
            </label>
            {f.projects.length > 1 && (
              <button onClick={() => removeRow("projects", i)} className="text-red-400 hover:text-red-300 text-xs flex items-center gap-1">
                <Trash2 size={13} /> Remove
              </button>
            )}
          </div>
        ))}
      </section>

      {/* Experience (optional) */}
      <section className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Experience (optional)</p>
          <button onClick={() => addRow("experience", emptyExp)} className="text-cyan-400 hover:text-cyan-300 text-xs flex items-center gap-1">
            <Plus size={13} /> Add
          </button>
        </div>
        {f.experience.map((row, i) => (
          <div key={i} className="space-y-2 rounded-xl bg-gray-950 border border-gray-800 p-3">
            <div className="grid sm:grid-cols-3 gap-2">
              <Field label="Role" value={row.role} onChange={(v) => setRow("experience", i, "role", v)} />
              <Field label="Company" value={row.company} onChange={(v) => setRow("experience", i, "company", v)} />
              <Field label="Duration" value={row.duration} onChange={(v) => setRow("experience", i, "duration", v)} />
            </div>
            <button onClick={() => removeRow("experience", i)} className="text-red-400 hover:text-red-300 text-xs flex items-center gap-1">
              <Trash2 size={13} /> Remove
            </button>
          </div>
        ))}
      </section>

      {/* JD tailoring (optional) */}
      <section className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
        <label className="block">
          <span className="text-[11px] uppercase tracking-[0.14em] text-gray-500">
            Target job description (optional — tailors wording)
          </span>
          <textarea
            value={f.job_description}
            onChange={(e) => set("job_description")(e.target.value)}
            rows={3}
            placeholder="Paste a JD to tailor the summary and bullet emphasis."
            className="mt-2 w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-cyan-700"
          />
        </label>
      </section>

      {error && <p className="text-sm text-red-400">{error}</p>}
      <Button size="lg" onClick={submit} disabled={drafting}>
        {drafting ? <Spinner size={16} /> : "Draft my resume with AI"}
      </Button>
    </div>
  );
}