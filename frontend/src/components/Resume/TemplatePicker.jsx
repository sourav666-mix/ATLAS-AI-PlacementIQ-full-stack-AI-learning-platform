// TemplatePicker.jsx - [NEW] Classic ATS / Modern / Technical
// FILE: frontend/src/components/Resume/TemplatePicker.jsx
// BATCH 29 / v10 Resume AI (new) - The 3 ReportLab templates + page count.

import React from "react";
import { Check } from "lucide-react";

const TEMPLATES = [
  { id: "classic", name: "Classic ATS", blurb: "Single column, maximum parse-ability." },
  { id: "modern", name: "Modern Minimal", blurb: "Clean hierarchy, subtle accents." },
  { id: "technical", name: "Technical Compact", blurb: "Dense, project-forward for engineers." },
];

export default function TemplatePicker({ template, pages, onTemplate, onPages }) {
  return (
    <div className="space-y-4">
      <div className="grid sm:grid-cols-3 gap-3">
        {TEMPLATES.map((t) => {
          const active = template === t.id;
          return (
            <button
              key={t.id}
              onClick={() => onTemplate(t.id)}
              className={`relative text-left rounded-xl border p-4 transition ${
                active ? "border-cyan-600 bg-cyan-950/30" : "border-gray-800 bg-gray-900 hover:border-gray-600"
              }`}
            >
              {active && (
                <span className="absolute top-2 right-2 h-4 w-4 rounded-full bg-cyan-500 text-gray-950 flex items-center justify-center">
                  <Check size={11} />
                </span>
              )}
              <p className="text-sm font-semibold text-gray-100">{t.name}</p>
              <p className="text-xs text-gray-500 mt-0.5">{t.blurb}</p>
            </button>
          );
        })}
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-400">Length:</span>
        {[1, 2].map((p) => (
          <button
            key={p}
            onClick={() => onPages(p)}
            className={`px-4 py-1.5 rounded-lg text-sm border transition ${
              pages === p ? "border-cyan-600 bg-cyan-950/30 text-cyan-200" : "border-gray-800 text-gray-300 hover:border-gray-600"
            }`}
          >
            {p} page{p > 1 ? "s" : ""}
          </button>
        ))}
      </div>
    </div>
  );
}