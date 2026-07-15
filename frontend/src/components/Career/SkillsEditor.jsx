/**
 * Labelled skills editor. Each skill = name + category + confidence label + details.
 * The "details / evidence" field is what un-caps a self-claim on the backend:
 * a skill named in a project or with evidence text is scored higher than one that isn't.
 */
import React, { useState } from "react";
import useCareerStore, { SKILL_LABELS, SKILL_CATEGORIES } from "../../store/careerStore";

const LABEL_COLOR = {
  beginner: "bg-slate-600",
  learning: "bg-sky-600",
  comfortable: "bg-emerald-600",
  strong: "bg-violet-600",
  expert: "bg-amber-500",
};

function SkillRow({ skill, index }) {
  const { updateSkill, removeSkill } = useCareerStore();
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <input
          value={skill.name}
          onChange={(e) => updateSkill(index, { name: e.target.value })}
          placeholder="Skill name"
          className="min-w-[120px] flex-1 rounded bg-slate-800 px-2 py-1 text-sm text-white outline-none"
        />
        <select
          value={skill.category}
          onChange={(e) => updateSkill(index, { category: e.target.value })}
          className="rounded bg-slate-800 px-2 py-1 text-xs text-slate-300 outline-none"
        >
          {SKILL_CATEGORIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <div className="flex overflow-hidden rounded border border-slate-700">
          {SKILL_LABELS.map((l) => (
            <button
              key={l}
              type="button"
              onClick={() => updateSkill(index, { label: l })}
              className={`px-2 py-1 text-[10px] capitalize transition ${
                skill.label === l
                  ? `${LABEL_COLOR[l]} text-white`
                  : "bg-slate-800 text-slate-500 hover:text-slate-300"
              }`}
            >
              {l}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="text-xs text-slate-500 hover:text-white"
        >
          {open ? "hide" : "details"}
        </button>
        <button
          type="button"
          onClick={() => removeSkill(index)}
          className="text-slate-600 hover:text-rose-400"
          aria-label="Remove skill"
        >
          ✕
        </button>
      </div>
      {open && (
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          <input
            value={skill.details || ""}
            onChange={(e) => updateSkill(index, { details: e.target.value })}
            placeholder="How well / how long (e.g. '3 semesters')"
            className="rounded bg-slate-800 px-2 py-1 text-xs text-white outline-none"
          />
          <input
            value={skill.evidence || ""}
            onChange={(e) => updateSkill(index, { evidence: e.target.value })}
            placeholder="Where you proved it (project, internship)"
            className="rounded bg-slate-800 px-2 py-1 text-xs text-white outline-none"
          />
        </div>
      )}
    </div>
  );
}

export default function SkillsEditor() {
  const { profile, addSkill } = useCareerStore();
  const [name, setName] = useState("");

  const add = () => {
    const n = name.trim();
    if (!n) return;
    addSkill({ name: n, category: "other", label: "learning", details: "", evidence: "" });
    setName("");
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-white">Current Skills</h3>
        <p className="text-xs text-slate-500">
          Be honest with the label — an un-proven “expert” is capped until a project backs it up.
        </p>
      </div>

      <div className="mb-3 flex gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder="Add a skill and press Enter"
          className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-600 outline-none focus:border-emerald-500"
        />
        <button
          type="button"
          onClick={add}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500"
        >
          Add
        </button>
      </div>

      <div className="space-y-2">
        {profile.skills.length === 0 && (
          <p className="py-4 text-center text-xs text-slate-600">No skills added yet.</p>
        )}
        {profile.skills.map((s, i) => (
          <SkillRow key={i} skill={s} index={i} />
        ))}
      </div>
    </div>
  );
}