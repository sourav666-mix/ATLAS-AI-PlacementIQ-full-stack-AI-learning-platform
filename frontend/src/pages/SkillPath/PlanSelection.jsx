// frontend/src/pages/SkillPath/PlanSelection.jsx
/**
 * ATLAS AI 4.0 - v12 SkillPath: STEP 2 - the plan, strictly second.
 * 3/6/9 months gate the roadmap phases deterministically
 * (Foundation+Core at 3, Advanced from 6). Commit -> roadmap.
 * Route: /skillpath/plan/:domainKey
 */

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import useSkillPathStore from "../../store/skillPathStore";

const PLANS = [
  { months: 3, title: "3 months", blurb: "Foundation + Core topics",
    detail: "The essentials - ideal if placements are close." },
  { months: 6, title: "6 months", blurb: "Everything incl. Advanced",
    detail: "The full roadmap, unlocked phase by phase.", featured: true },
  { months: 9, title: "9 months", blurb: "Full roadmap, relaxed pace",
    detail: "Same content, more runway - start early, go deep." },
];

export default function PlanSelection() {
  const navigate = useNavigate();
  const { domainKey } = useParams();
  const { domains, pendingDomainKey, chooseDomain, commitPlan, error } =
    useSkillPathStore();
  const [busy, setBusy] = useState(null);

  useEffect(() => {
    // deep-link safety: /skillpath/plan/:domainKey without step 1
    if (!pendingDomainKey && domainKey) chooseDomain(domainKey);
  }, [pendingDomainKey, domainKey, chooseDomain]);

  const card = domains.find((d) => d.key === (pendingDomainKey || domainKey));

  const pick = async (months) => {
    setBusy(months);
    const res = await commitPlan(months);
    setBusy(null);
    if (res) navigate(`/skillpath/roadmap/${res.domain_id}`);
  };

  return (
    <div className="mx-auto max-w-3xl p-6">
      <header className="mb-6">
        <p className="text-xs uppercase tracking-wide text-sky-400">
          {card ? card.name : "Your track"}
        </p>
        <h1 className="text-2xl font-bold text-zinc-100">How long do you have?</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Plans gate how much of the roadmap opens - the content is the
          same locked curriculum either way.
        </p>
      </header>

      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {PLANS.map((p) => (
          <button
            key={p.months}
            type="button"
            disabled={busy !== null}
            onClick={() => pick(p.months)}
            className={`rounded-xl border p-4 text-left transition
                        ${p.featured
                          ? "border-sky-600 bg-sky-950/30"
                          : "border-zinc-800 bg-zinc-900 hover:border-sky-700"}`}
          >
            <div className="text-xl font-bold text-zinc-100">
              {busy === p.months ? "…" : p.title}
            </div>
            <div className="mt-1 text-sm text-sky-300">{p.blurb}</div>
            <p className="mt-2 text-xs text-zinc-500">{p.detail}</p>
          </button>
        ))}
      </div>

      <button type="button" onClick={() => navigate("/skillpath")}
        className="mt-6 text-xs text-zinc-500 hover:text-zinc-300">
        ← change track
      </button>
    </div>
  );
}