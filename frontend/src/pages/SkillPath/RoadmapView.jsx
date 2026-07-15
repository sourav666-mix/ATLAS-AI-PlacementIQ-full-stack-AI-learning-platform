// frontend/src/pages/SkillPath/RoadmapView.jsx
/**
 * ATLAS AI 4.0 - v12 SkillPath: STEP 3 - the roadmap.
 * Ordered topic cards with a deterministic progress ring and status
 * color: grey locked / blue current / green complete. Live Lab Pro sits
 * one click away (spec: "Live Lab beside the roadmap").
 * Route: /skillpath/roadmap/:domainId
 */

import { useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import useSkillPathStore from "../../store/skillPathStore";

export function ProgressRing({ pct, size = 44, stroke = 4, status }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const color =
    status === "complete" ? "#22c55e"
    : status === "current" ? "#38bdf8" : "#52525b";
  return (
    <svg width={size} height={size} role="img" aria-label={`${pct}% complete`}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none"
              stroke="#27272a" strokeWidth={stroke} />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none"
              stroke={color} strokeWidth={stroke} strokeLinecap="round"
              strokeDasharray={c} strokeDashoffset={c * (1 - pct / 100)}
              transform={`rotate(-90 ${size / 2} ${size / 2})`} />
      <text x="50%" y="54%" dominantBaseline="middle" textAnchor="middle"
            fill="#e4e4e7" fontSize={size / 4}>{pct}%</text>
    </svg>
  );
}

const STATUS_STYLE = {
  complete: "border-emerald-700/70",
  current: "border-sky-600",
  locked: "border-zinc-800 opacity-60",
};

export default function RoadmapView() {
  const navigate = useNavigate();
  const { domainId } = useParams();
  const { roadmap, loadRoadmap, loadingRoadmap, error } = useSkillPathStore();

  useEffect(() => {
    if (domainId) loadRoadmap(domainId);
  }, [domainId, loadRoadmap]);

  const openTopic = (t) => {
    if (t.status === "locked") return;
    navigate(`/skillpath/topic/${t.topic_id}/learn?domain=${domainId}`);
  };

  return (
    <div className="mx-auto max-w-4xl p-6">
      <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-sky-400">
            {roadmap?.domain_name || "Roadmap"} · {roadmap?.plan_months}-month plan
          </p>
          <h1 className="text-2xl font-bold text-zinc-100">Your roadmap</h1>
        </div>
        <div className="flex items-center gap-3">
          {roadmap && (
            <span className="text-sm text-zinc-400">
              overall <span className="text-zinc-100">{roadmap.overall_pct}%</span>
            </span>
          )}
          <Link to="/labpro"
                className="rounded-md border border-zinc-700 px-3 py-1.5 text-xs
                           text-zinc-200 hover:border-sky-600 hover:text-sky-300">
            🧪 Live Lab Pro
          </Link>
        </div>
      </header>

      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}
      {loadingRoadmap && <p className="text-sm text-zinc-500">Loading…</p>}

      <ol className="space-y-3">
        {roadmap?.topics.map((t) => (
          <li key={t.topic_id}>
            <button
              type="button"
              onClick={() => openTopic(t)}
              disabled={t.status === "locked"}
              className={`flex w-full items-center gap-4 rounded-xl border
                          bg-zinc-900 p-4 text-left transition
                          ${STATUS_STYLE[t.status]}
                          ${t.status !== "locked" ? "hover:bg-zinc-900/70" : "cursor-not-allowed"}`}
            >
              <ProgressRing pct={t.progress_pct} status={t.status} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate font-semibold text-zinc-100">
                    {t.item_order + 1}. {t.title}
                  </span>
                  {t.status === "complete" && <span className="text-emerald-400">✓</span>}
                  {t.status === "locked" && <span className="text-zinc-500">🔒</span>}
                </div>
                <p className="mt-0.5 text-xs text-zinc-500">
                  {t.phase} · {t.subtopics_mastered}/{t.subtopic_total} skills
                  mastered · ~{t.est_hours}h
                </p>
              </div>
              {t.status === "current" && (
                <span className="shrink-0 rounded bg-sky-700 px-2 py-1 text-[11px]
                                 font-semibold text-white">
                  Continue →
                </span>
              )}
            </button>
          </li>
        ))}
      </ol>

      {roadmap && roadmap.topics.some((t) => t.status === "locked") && (
        <p className="mt-4 text-[11px] text-zinc-600">
          🔒 Locked topics open as you complete the ones before them - and
          Advanced-phase topics need the 6-month plan or longer.
        </p>
      )}
    </div>
  );
}