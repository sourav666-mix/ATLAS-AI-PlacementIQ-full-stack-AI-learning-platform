/**
 * LeetCode volume input. Feeds the DSA pillar directly.
 * Shows a live weighted estimate so the student sees why the number matters.
 */
import React from "react";
import useCareerStore from "../../store/careerStore";

function Stepper({ label, value, onChange, accent }) {
  const set = (v) => onChange(Math.max(0, Math.min(3000, v)));
  return (
    <div className="flex-1">
      <div className="mb-1 flex items-center gap-2 text-xs font-medium text-slate-400">
        <span className={`h-2 w-2 rounded-full ${accent}`} />
        {label}
      </div>
      <div className="flex items-center rounded-lg border border-slate-700 bg-slate-900">
        <button
          type="button"
          onClick={() => set(Number(value) - 1)}
          className="px-3 py-2 text-slate-400 hover:text-white"
        >
          −
        </button>
        <input
          type="number"
          min={0}
          value={value}
          onChange={(e) => set(parseInt(e.target.value || "0", 10))}
          className="w-full bg-transparent text-center text-lg font-semibold text-white outline-none"
        />
        <button
          type="button"
          onClick={() => set(Number(value) + 1)}
          className="px-3 py-2 text-slate-400 hover:text-white"
        >
          +
        </button>
      </div>
    </div>
  );
}

export default function LeetCodeInput() {
  const { profile, setField } = useCareerStore();
  const e = Number(profile.leetcode_easy) || 0;
  const m = Number(profile.leetcode_medium) || 0;
  const h = Number(profile.leetcode_hard) || 0;

  // mirror of backend score_dsa() for a live preview (server remains source of truth)
  const weighted = e * 1 + m * 2.5 + h * 5;
  const estimate = Math.max(0, Math.min(100, Math.round(weighted / 4.5)));

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white">LeetCode Solved</h3>
          <p className="text-xs text-slate-500">
            Your DSA pillar is computed from these — Medium and Hard count most.
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-emerald-400">{estimate}</div>
          <div className="text-[10px] uppercase tracking-wide text-slate-500">
            est. DSA score
          </div>
        </div>
      </div>

      <input
        type="text"
        value={profile.leetcode_username}
        onChange={(ev) => setField("leetcode_username", ev.target.value)}
        placeholder="LeetCode username (optional)"
        className="mb-4 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-600 outline-none focus:border-emerald-500"
      />

      <div className="flex gap-3">
        <Stepper
          label="Easy"
          value={profile.leetcode_easy}
          onChange={(v) => setField("leetcode_easy", v)}
          accent="bg-emerald-500"
        />
        <Stepper
          label="Medium"
          value={profile.leetcode_medium}
          onChange={(v) => setField("leetcode_medium", v)}
          accent="bg-amber-500"
        />
        <Stepper
          label="Hard"
          value={profile.leetcode_hard}
          onChange={(v) => setField("leetcode_hard", v)}
          accent="bg-rose-500"
        />
      </div>
    </div>
  );
}