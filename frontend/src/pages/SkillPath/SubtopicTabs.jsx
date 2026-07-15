// frontend/src/components/SkillPath/SubtopicTabs.jsx
/**
 * ATLAS AI 4.0 - v12 SkillPath: STEPS 5-6 - the subtopic tabs.
 * One tab per subtopic in the founder's order; a green tick appears at
 * mastery (>=20/25 correct - deterministic, computed server-side).
 */

import useSkillPathStore from "../../store/skillPathStore";

export default function SubtopicTabs() {
  const { tabs, activeSubtopicId, selectSubtopic } = useSkillPathStore();
  if (!tabs) return null;

  return (
    <div className="border-b border-zinc-800">
      <div className="flex gap-1 overflow-x-auto pb-px">
        {tabs.tabs.map((t) => (
          <button
            key={t.subtopic_id}
            type="button"
            onClick={() => selectSubtopic(t.subtopic_id)}
            title={`${t.correct}/${t.answered} correct · bank of ${t.bank_size}`}
            className={`shrink-0 rounded-t-md px-3 py-2 text-xs transition
                        ${activeSubtopicId === t.subtopic_id
                          ? "border border-b-0 border-zinc-700 bg-zinc-900 text-sky-300"
                          : "text-zinc-400 hover:bg-zinc-900/60"}`}
          >
            {t.name}
            {t.mastered ? (
              <span className="ml-1 text-emerald-400">✓</span>
            ) : t.answered > 0 ? (
              <span className="ml-1 text-zinc-500">{t.mastery_pct}%</span>
            ) : null}
          </button>
        ))}
      </div>
      {tabs.all_mastered && (
        <p className="px-1 pb-2 text-xs text-emerald-400">
          🎉 Every skill in {tabs.topic_title} is mastered - this topic is
          green on your roadmap.
        </p>
      )}
    </div>
  );
}