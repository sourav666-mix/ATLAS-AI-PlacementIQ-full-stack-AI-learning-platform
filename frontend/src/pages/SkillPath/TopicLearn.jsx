// frontend/src/pages/SkillPath/TopicLearn.jsx
/**
 * ATLAS AI 4.0 - v12 SkillPath: STEP 4 - LEARN mode.
 * Topic overview + per-subtopic explainer (what/when/how + exactly five
 * worked examples, seeded server-side, zero AI). The big PRACTICE button
 * hands over to the arena; Live Lab is one click for free-form tinkering.
 * Route: /skillpath/topic/:topicId/learn?domain=<domainId>
 */

import { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import useSkillPathStore from "../../store/skillPathStore";
import VizMount from "../../components/Viz/VizMount";

function Example({ ex, index }) {
  return (
    <details className="rounded-md border border-zinc-800 bg-zinc-950/60">
      <summary className="cursor-pointer px-3 py-2 text-sm text-zinc-200">
        {index + 1}. {ex.title}
      </summary>
      <div className="space-y-2 px-3 pb-3">
        {ex.code && (
          <pre className="overflow-auto rounded bg-zinc-950 p-2 font-mono text-xs text-sky-200">
            {ex.code}
          </pre>
        )}
        {ex.output && (
          <pre className="overflow-auto rounded bg-zinc-900 p-2 font-mono text-xs text-zinc-300">
            {ex.output}
          </pre>
        )}
        {ex.why && <p className="text-xs text-zinc-400">💡 {ex.why}</p>}
      </div>
    </details>
  );
}

export default function TopicLearn() {
  const navigate = useNavigate();
  const { topicId } = useParams();
  const [params] = useSearchParams();
  const domainId = params.get("domain");
  const { learn, loadLearn, loadingLearn, error } = useSkillPathStore();
  const [openSubtopic, setOpenSubtopic] = useState(null);

  useEffect(() => {
    if (topicId) loadLearn(topicId);
  }, [topicId, loadLearn]);

  const goPractice = () =>
    navigate(`/skillpath/topic/${topicId}/practice?domain=${domainId}`);

  return (
    <div className="mx-auto max-w-3xl p-6">
      <button type="button" onClick={() => navigate(-1)}
        className="mb-3 text-xs text-zinc-500 hover:text-zinc-300">← roadmap</button>

      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}
      {loadingLearn && <p className="text-sm text-zinc-500">Loading…</p>}

      {learn && (
        <>
          <header className="mb-4">
            <h1 className="text-2xl font-bold text-zinc-100">{learn.title}</h1>
            <p className="mt-2 text-sm leading-6 text-zinc-300">{learn.overview}</p>
            <div className="mt-3">
              <VizMount kind={learn.viz_kind} />
            </div>
          </header>

          <div className="sticky top-2 z-10 mb-5 flex gap-2">
            <button type="button" onClick={goPractice}
              className="flex-1 rounded-lg bg-sky-600 py-2.5 text-sm font-semibold
                         text-white shadow hover:bg-sky-500">
              PRACTICE →
            </button>
            <Link to="/labpro"
                  className="rounded-lg border border-zinc-700 px-4 py-2.5 text-sm
                             text-zinc-200 hover:border-sky-600">
              🧪 Lab
            </Link>
          </div>

          <ol className="space-y-3">
            {learn.subtopics.map((st) => (
              <li key={st.subtopic_id}
                  className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
                <button type="button"
                        onClick={() => setOpenSubtopic(
                          openSubtopic === st.subtopic_id ? null : st.subtopic_id)}
                        className="flex w-full items-center justify-between text-left">
                  <span className="font-semibold text-zinc-100">{st.name}</span>
                  <span className="text-zinc-500">
                    {openSubtopic === st.subtopic_id ? "−" : "+"}
                  </span>
                </button>

                {openSubtopic === st.subtopic_id && (
                  <div className="mt-3 space-y-3 text-sm leading-6">
                    <div>
                      <h3 className="text-xs font-semibold uppercase text-sky-400">What it is</h3>
                      <p className="text-zinc-300">{st.what_it_is}</p>
                    </div>
                    {st.when_to_use && (
                      <div>
                        <h3 className="text-xs font-semibold uppercase text-sky-400">When to use it</h3>
                        <p className="text-zinc-300">{st.when_to_use}</p>
                      </div>
                    )}
                    {st.how_to_use && (
                      <div>
                        <h3 className="text-xs font-semibold uppercase text-sky-400">How to use it</h3>
                        <p className="text-zinc-300">{st.how_to_use}</p>
                      </div>
                    )}
                    <div>
                      <h3 className="mb-1 text-xs font-semibold uppercase text-sky-400">
                        Five worked examples
                      </h3>
                      <div className="space-y-2">
                        {st.examples.map((ex, i) => (
                          <Example key={i} ex={ex} index={i} />
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  );
}