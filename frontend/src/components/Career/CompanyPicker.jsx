/**
 * Target company picker (max 3). Shows the archetype and hiring bar so the
 * student understands why Amazon and TCS demand different things.
 */
import React from "react";
import useCareerStore from "../../store/careerStore";

const ARCHETYPE_LABEL = {
  product_faang: "Top Product",
  product_mid: "Product",
  service_mass: "Service / Mass",
  consulting: "Consulting",
  product: "Product",
};

function BarPips({ level }) {
  const filled = Math.round((level / 100) * 5);
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <span
          key={i}
          className={`h-1.5 w-4 rounded-full ${
            i < filled ? "bg-emerald-500" : "bg-slate-700"
          }`}
        />
      ))}
    </div>
  );
}

export default function CompanyPicker() {
  const { companies, profile, toggleTarget, loadingCompanies } = useCareerStore();
  const selected = new Set(profile.targets.map((t) => t.company_slug));

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white">Target Companies</h3>
          <p className="text-xs text-slate-500">Pick up to 3. Your dream company first.</p>
        </div>
        <span className="text-xs font-medium text-emerald-400">
          {profile.targets.length}/3 selected
        </span>
      </div>

      {loadingCompanies ? (
        <p className="py-6 text-center text-sm text-slate-500">Loading companies…</p>
      ) : companies.length === 0 ? (
        <p className="py-6 text-center text-sm text-slate-500">
          No companies for this domain yet.
        </p>
      ) : (
        <div className="grid gap-2 sm:grid-cols-2">
          {companies.map((c) => {
            const isOn = selected.has(c.company_slug);
            const disabled = !isOn && profile.targets.length >= 3;
            const priority =
              profile.targets.find((t) => t.company_slug === c.company_slug)?.priority;
            return (
              <button
                key={c.company_slug}
                type="button"
                disabled={disabled}
                onClick={() => toggleTarget(c.company_slug)}
                className={`rounded-lg border p-3 text-left transition ${
                  isOn
                    ? "border-emerald-500 bg-emerald-500/10"
                    : disabled
                    ? "cursor-not-allowed border-slate-800 bg-slate-900/40 opacity-40"
                    : "border-slate-700 bg-slate-900 hover:border-slate-500"
                }`}
              >
                <div className="flex items-start justify-between">
                  <span className="font-medium text-white">{c.company_name}</span>
                  {isOn && (
                    <span className="rounded-full bg-emerald-500 px-2 py-0.5 text-[10px] font-bold text-slate-900">
                      #{priority}
                    </span>
                  )}
                </div>
                <div className="mt-1 text-[11px] text-slate-500">
                  {ARCHETYPE_LABEL[c.archetype] || c.archetype}
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-[10px] text-slate-500">bar</span>
                  <BarPips level={c.hiring_bar} />
                  <span className="text-[10px] text-slate-500">{c.hiring_bar}</span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}