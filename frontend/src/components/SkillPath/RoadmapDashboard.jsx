// frontend/src/components/SkillPath/RoadmapDashboard.jsx   [MOD v12 — was RoadmapTrack.jsx]
// Progress ring + topic timeline (grey/blue/green), each topic expands into SubtopicPills.
// Opening a subtopic pill routes into its Learn Card (the only path into Practice).
import { useEffect, useState } from "react";
import { useSkillpathStore } from "../../store/skillpathV3Store";
import SubtopicPills from "./SubtopicPills";
import TopicLearnCard from "./TopicLearnCard";

function ProgressRing({ pct }) {
  const R = 46;
  const C = 2 * Math.PI * R;
  const offset = C - (Math.min(100, Math.max(0, pct)) / 100) * C;
  return (
    <svg width="120" height="120" viewBox="0 0 120 120" className="shrink-0">
      <circle cx="60" cy="60" r={R} fill="none" stroke="#27272a" strokeWidth="10" />
      <circle
        cx="60" cy="60" r={R} fill="none" stroke="#8b5cf6" strokeWidth="10"
        strokeLinecap="round" strokeDasharray={C} strokeDashoffset={offset}
        transform="rotate(-90 60 60)" style={{ transition: "stroke-dashoffset .6s ease" }}
      />
      <text x="60" y="66" textAnchor="middle" className="fill-zinc-100 text-xl font-semibold">
        {pct}%
      </text>
    </svg>
  );
}

const STATE_DOT = { grey: "bg-zinc-600", blue: "bg-violet-500", green: "bg-emerald-500" };

export default function RoadmapDashboard({ domainId, planMonths, onOpenTopic }) {
  const { roadmap, loading, error, loadRoadmap } = useSkillpathStore();
  const [openTopic, setOpenTopic] = useState(null);
  const [activeSubtopic, setActiveSubtopic] = useState(null);

  useEffect(() => {
    if (domainId) loadRoadmap(domainId, planMonths);
  }, [domainId, planMonths, loadRoadmap]);

  if (loading) return <p className="text-zinc-500">Loading roadmap…</p>;
  if (error) return <p className="text-rose-400">{error}</p>;
  if (!roadmap) return null;

  // A subtopic is open -> show its Learn Card (teach-before-practice)
  if (activeSubtopic) {
    return (
      <TopicLearnCard
        subtopicId={activeSubtopic}
        onBack={() => setActiveSubtopic(null)}
      />
    );
  }

  return (
    <div>
      <div className="flex items-center gap-6 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6">
        <ProgressRing pct={roadmap.progress_pct} />
        <div>
          <h2 className="text-2xl font-semibold">{roadmap.domain_name}</h2>
          <p className="text-zinc-400 mt-1">
            {roadmap.plan_months}-month track · {roadmap.topics.length} topics
          </p>
        </div>
      </div>

      <ol className="mt-6 space-y-3">
        {roadmap.topics.map((t, i) => {
          const isOpen = openTopic === t.topic_id;
          return (
            <li key={t.topic_id} className="rounded-2xl border border-zinc-800 bg-zinc-900/60">
              <button
                onClick={() => {
                  const next = isOpen ? null : t.topic_id;
                  setOpenTopic(next);
                  onOpenTopic?.(next);
                }}
                className="w-full flex items-center gap-4 px-5 py-4 text-left"
              >
                <span className={`h-2.5 w-2.5 rounded-full ${STATE_DOT[t.state]}`} />
                <span className="text-zinc-500 text-sm w-6">{i + 1}</span>
                <span className="font-medium flex-1">{t.title}</span>
                {t.is_shared_module && (
                  <span className="text-[11px] rounded bg-zinc-800 text-zinc-400 px-2 py-0.5">
                    shared module
                  </span>
                )}
                <span className="text-zinc-500">{isOpen ? "▾" : "▸"}</span>
              </button>
              {isOpen && (
                <div className="px-5 pb-5">
                  <SubtopicPills pills={t.subtopics} onSelect={setActiveSubtopic} />
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}