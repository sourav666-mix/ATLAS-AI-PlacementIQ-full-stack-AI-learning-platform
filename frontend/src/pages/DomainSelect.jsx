// FILE: frontend/src/pages/DomainSelect.jsx
// v12 — the new SkillPath entry screen: pick a career domain, then a plan length.
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSkillpathStore } from "../store/skillpathV3Store";

const PLAN_TIERS = [
  { months: 3, label: "3-Month Sprint", depth: "Foundation + Core" },
  { months: 6, label: "6-Month Career Track", depth: "+ Advanced" },
  { months: 9, label: "9-Month Mastery Track", depth: "+ Specialization + Capstones" },
];

export default function DomainSelect() {
  const navigate = useNavigate();
  const { domains, loading, error, loadDomains } = useSkillpathStore();
  const [picked, setPicked] = useState(null);

  useEffect(() => {
    loadDomains();
  }, [loadDomains]);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-100">Choose your career domain</h1>
      <p className="text-sm text-gray-500 mt-1">
        Pick what you want to become. You'll set your plan length next.
      </p>

      {loading && <p className="mt-6 text-gray-500">Loading domains…</p>}
      {error && <p className="mt-6 text-red-400">{error}</p>}
      {!loading && !error && domains.length === 0 && (
        <p className="mt-6 text-gray-500">
          No domains found. Run the seed scripts, then refresh.
        </p>
      )}

      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {domains.map((d) => (
          <button
            key={d.id}
            onClick={() => setPicked(d)}
            className="text-left rounded-xl border border-gray-800 bg-gray-900 p-5 hover:border-violet-500 transition-colors"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-100">{d.name}</h3>
              <span className="text-xs rounded-full bg-violet-500/10 text-violet-300 px-2 py-0.5">
                {d.students_on_path ?? 0} enrolled
              </span>
            </div>
            <p className="mt-2 text-sm text-gray-500">
              {d.pitch || "Structured roadmap, hands-on labs, AI-graded practice."}
            </p>
            <span className="mt-4 inline-block text-sm text-violet-400">Select →</span>
          </button>
        ))}
      </div>

      {picked && (
        <div
          className="fixed inset-0 z-40 bg-black/60 flex items-center justify-center p-4"
          onClick={() => setPicked(null)}
        >
          <div
            className="w-full max-w-md rounded-xl border border-gray-800 bg-gray-900 p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-xl font-semibold text-gray-100">
              {picked.name} — choose your plan
            </h2>
            <div className="mt-4 space-y-3">
              {PLAN_TIERS.map((t) => (
                <button
                  key={t.months}
                  onClick={() => navigate(`/roadmap/${picked.id}?plan=${t.months}`)}
                  className="w-full flex items-center justify-between rounded-lg border border-gray-800 bg-gray-950 px-4 py-3 hover:border-violet-500 transition-colors"
                >
                  <span className="font-medium text-gray-100">{t.label}</span>
                  <span className="text-sm text-gray-500">{t.depth}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}