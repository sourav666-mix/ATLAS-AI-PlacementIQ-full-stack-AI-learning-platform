// LivePreview.jsx - [NEW] editable resume preview
// FILE: frontend/src/components/Resume/LivePreview.jsx
// BATCH 29 / v10 Resume AI (new) - The edit loop: the AI draft renders as an
// editable preview. Every generated line (summary, bullets, skills) is an
// inline-editable field so the student can fix wording before export. The
// edited draft is what gets typeset — nothing is locked by the AI.

import React, { useEffect, useState } from "react";

function Editable({ value, onChange, className = "", multiline = false, placeholder }) {
  const common =
    "w-full bg-transparent border border-transparent hover:border-gray-800 focus:border-cyan-700 rounded px-2 py-1 text-gray-200 focus:outline-none transition";
  return multiline ? (
    <textarea
      value={value || ""}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={2}
      className={`${common} resize-y ${className}`}
    />
  ) : (
    <input
      value={value || ""}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className={`${common} ${className}`}
    />
  );
}

export default function LivePreview({ draft, onChange }) {
  const [d, setD] = useState(draft || {});

  useEffect(() => setD(draft || {}), [draft]);

  const update = (patch) => {
    const next = { ...d, ...patch };
    setD(next);
    onChange(next);
  };
  const updateBullet = (projIndex, bulletIndex, value) => {
    const projects = [...(d.projects || [])];
    const bullets = [...(projects[projIndex].bullets || [])];
    bullets[bulletIndex] = value;
    projects[projIndex] = { ...projects[projIndex], bullets };
    update({ projects });
  };

  return (
    <div className="bg-white text-gray-900 rounded-2xl p-8 shadow-xl max-w-2xl mx-auto">
      {/* Header */}
      <Editable
        value={d.full_name}
        onChange={(v) => update({ full_name: v })}
        className="!text-2xl !font-bold !text-gray-900 text-center"
        placeholder="Your Name"
      />
      <p className="text-center text-sm text-gray-600 mb-4">
        {[d.email, d.phone, d.address].filter(Boolean).join(" · ")}
      </p>

      {/* Summary */}
      <section className="mb-4">
        <h3 className="text-xs font-bold uppercase tracking-wide text-gray-500 border-b border-gray-300 mb-1">Summary</h3>
        <Editable
          value={d.summary}
          onChange={(v) => update({ summary: v })}
          multiline
          className="!text-sm !text-gray-800"
          placeholder="AI-drafted professional summary…"
        />
      </section>

      {/* Skills */}
      {d.skills && (
        <section className="mb-4">
          <h3 className="text-xs font-bold uppercase tracking-wide text-gray-500 border-b border-gray-300 mb-1">Skills</h3>
          <Editable
            value={Array.isArray(d.skills) ? d.skills.join(", ") : d.skills}
            onChange={(v) => update({ skills: v.split(",").map((s) => s.trim()) })}
            className="!text-sm !text-gray-800"
          />
        </section>
      )}

      {/* Projects */}
      {(d.projects || []).length > 0 && (
        <section className="mb-4">
          <h3 className="text-xs font-bold uppercase tracking-wide text-gray-500 border-b border-gray-300 mb-1">Projects</h3>
          {(d.projects || []).map((p, i) => (
            <div key={i} className="mb-2">
              <p className="text-sm font-semibold text-gray-900">{p.name} {p.tech && <span className="font-normal text-gray-600">· {p.tech}</span>}</p>
              {(p.bullets || []).map((b, bi) => (
                <div key={bi} className="flex gap-1 items-start">
                  <span className="text-gray-500 mt-1.5 text-xs">•</span>
                  <Editable
                    value={b}
                    onChange={(v) => updateBullet(i, bi, v)}
                    className="!text-sm !text-gray-800"
                  />
                </div>
              ))}
            </div>
          ))}
        </section>
      )}

      {/* Education */}
      {(d.education || []).length > 0 && (
        <section>
          <h3 className="text-xs font-bold uppercase tracking-wide text-gray-500 border-b border-gray-300 mb-1">Education</h3>
          {(d.education || []).map((e, i) => (
            <p key={i} className="text-sm text-gray-800">
              {[e.degree, e.institution, e.year, e.score].filter(Boolean).join(" · ")}
            </p>
          ))}
        </section>
      )}
    </div>
  );
}