// frontend/src/pages/SkillPath/DomainSelection.jsx
/**
 * ATLAS AI 4.0 - v12 SkillPath: STEP 1 - choose your world first.
 * Nine locked cards, each selling the destination: roles, example
 * companies, and the size of the question bank waiting inside.
 * Route: /skillpath
 */

import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useSkillPathStore from "../../store/skillPathStore";

export default function DomainSelection() {
  const navigate = useNavigate();
  const { domains, loadDomains, chooseDomain, loadingDomains, error } =
    useSkillPathStore();

  useEffect(() => {
    loadDomains();
  }, [loadDomains]);

  const pick = (d) => {
    chooseDomain(d.key);
    navigate(`/skillpath/plan/${d.key}`);
  };

  return (
    <div className="mx-auto max-w-5xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-zinc-100">
          Pick your placement track
        </h1>
        <p className="mt-1 text-sm text-zinc-400">
          Choose the world you want to work in - the plan comes after.
        </p>
      </header>

      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}
      {loadingDomains && <p className="text-sm text-zinc-500">Loading…</p>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {domains.map((d) => (
          <button
            key={d.key}
            type="button"
            onClick={() => pick(d)}
            className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-left
                       transition hover:border-sky-600 hover:bg-zinc-900/70"
          >
            <div className="text-lg font-semibold text-zinc-100">{d.name}</div>
            <p className="mt-1 text-xs text-zinc-400">{d.tagline}</p>

            <div className="mt-3 flex flex-wrap gap-1">
              {d.roles.slice(0, 3).map((r) => (
                <span key={r}
                      className="rounded bg-sky-950/60 px-2 py-0.5 text-[11px] text-sky-300">
                  {r}
                </span>
              ))}
            </div>

            <p className="mt-2 text-[11px] text-zinc-500">
              hiring: {d.example_companies.join(" · ")}
            </p>

            <div className="mt-3 border-t border-zinc-800 pt-2 text-[11px] text-zinc-500">
              {d.topic_count} topics · {d.subtopic_sets} skill sets ·{" "}
              <span className="text-zinc-300">{d.question_bank.toLocaleString()} questions</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}