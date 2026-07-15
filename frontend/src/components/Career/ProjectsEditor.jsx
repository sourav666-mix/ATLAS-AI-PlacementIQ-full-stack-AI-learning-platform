/**
 * Projects editor. Explicit "deployed?" toggle is intentional:
 * a project that is built but NOT deployed still counts — it just doesn't earn
 * the deployment pillar. This is the exact case in the brief ("project but not deploy").
 */
import React, { useState } from "react";
import useCareerStore from "../../store/careerStore";

function TechChips({ tech, onChange }) {
  const [val, setVal] = useState("");
  const add = () => {
    const t = val.trim();
    if (t && !tech.includes(t)) onChange([...tech, t]);
    setVal("");
  };
  return (
    <div>
      <div className="mb-1 flex flex-wrap gap-1">
        {tech.map((t) => (
          <span
            key={t}
            className="inline-flex items-center gap-1 rounded bg-slate-800 px-2 py-0.5 text-[11px] text-slate-300"
          >
            {t}
            <button
              type="button"
              onClick={() => onChange(tech.filter((x) => x !== t))}
              className="text-slate-500 hover:text-rose-400"
            >
              ✕
            </button>
          </span>
        ))}
      </div>
      <input
        value={val}
        onChange={(e) => setVal(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), add())}
        placeholder="Add tech (Enter)"
        className="w-full rounded bg-slate-800 px-2 py-1 text-xs text-white outline-none"
      />
    </div>
  );
}

function ProjectCard({ project, index }) {
  const { updateProject, removeProject } = useCareerStore();
  const p = project;
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <div className="mb-2 flex items-center gap-2">
        <input
          value={p.title}
          onChange={(e) => updateProject(index, { title: e.target.value })}
          placeholder="Project title"
          className="flex-1 rounded bg-slate-800 px-2 py-1 text-sm font-medium text-white outline-none"
        />
        <button
          type="button"
          onClick={() => removeProject(index)}
          className="text-slate-600 hover:text-rose-400"
        >
          ✕
        </button>
      </div>

      <textarea
        value={p.description || ""}
        onChange={(e) => updateProject(index, { description: e.target.value })}
        placeholder="What it does, the dataset/scope, your role. Longer, specific descriptions score higher."
        rows={2}
        className="mb-2 w-full rounded bg-slate-800 px-2 py-1 text-xs text-white outline-none"
      />

      <div className="mb-2">
        <TechChips
          tech={p.tech || []}
          onChange={(tech) => updateProject(index, { tech })}
        />
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        <input
          value={p.github || ""}
          onChange={(e) => updateProject(index, { github: e.target.value })}
          placeholder="GitHub URL"
          className="rounded bg-slate-800 px-2 py-1 text-xs text-white outline-none"
        />
        <input
          value={p.metrics || ""}
          onChange={(e) => updateProject(index, { metrics: e.target.value })}
          placeholder="Impact (e.g. 94% accuracy, 40k rows)"
          className="rounded bg-slate-800 px-2 py-1 text-xs text-white outline-none"
        />
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-xs text-slate-300">
          <input
            type="checkbox"
            checked={!!p.deployed}
            onChange={(e) =>
              updateProject(index, {
                deployed: e.target.checked,
                deployed_url: e.target.checked ? p.deployed_url || "" : "",
              })
            }
            className="accent-emerald-500"
          />
          Deployed / live
        </label>
        {p.deployed ? (
          <input
            value={p.deployed_url || ""}
            onChange={(e) => updateProject(index, { deployed_url: e.target.value })}
            placeholder="Live URL (unlocks full deployment credit)"
            className="flex-1 rounded bg-slate-800 px-2 py-1 text-xs text-white outline-none"
          />
        ) : (
          <span className="text-[11px] text-amber-500/80">
            Not deployed yet — ATLAS will put “ship it” on your plan.
          </span>
        )}
      </div>
    </div>
  );
}

export default function ProjectsEditor() {
  const { profile, addProject } = useCareerStore();
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white">Projects</h3>
          <p className="text-xs text-slate-500">
            Built-but-not-deployed is fine — it still counts toward your portfolio.
          </p>
        </div>
        <button
          type="button"
          onClick={() =>
            addProject({
              title: "",
              description: "",
              tech: [],
              github: "",
              deployed: false,
              deployed_url: "",
              metrics: "",
            })
          }
          className="rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-500"
        >
          + Project
        </button>
      </div>

      <div className="space-y-3">
        {profile.projects.length === 0 && (
          <p className="py-4 text-center text-xs text-slate-600">No projects added yet.</p>
        )}
        {profile.projects.map((p, i) => (
          <ProjectCard key={i} project={p} index={i} />
        ))}
      </div>
    </div>
  );
}