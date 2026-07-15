// frontend/src/pages/SkillPath/PracticeArena.jsx
/**
 * ATLAS AI 4.0 - v12 SkillPath: STEP 7 - the subtopic Code Arena.
 *
 * Question + exactly TWO worked examples + an answer editor. Code and SQL
 * questions run on the SAME Live Lab kernel (one kernel, three surfaces) -
 * students test before submitting, and the run output rides along to the
 * analyzer. Submit fires the ONE Type B call; the AnalysisCard reveals
 * the model solution only after. The progress strip and difficulty badge
 * are pure server math.
 * Route: /skillpath/topic/:topicId/practice?domain=<domainId>
 */

import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import useSkillPathStore from "../../store/skillPathStore";
import SubtopicTabs from "./SubtopicTabs";
import AnalysisCard from "./AnalysisCard";
import CellEditor from "../../components/LabPro/CellEditor";
import kernel from "../../components/LabPro/labProKernel";

const DIFF_STYLE = {
  basic: "bg-emerald-950/60 text-emerald-300",
  medium: "bg-amber-950/60 text-amber-300",
  advanced: "bg-red-950/60 text-red-300",
};

export default function PracticeArena() {
  const navigate = useNavigate();
  const { topicId } = useParams();
  const [params] = useSearchParams();
  const domainId = params.get("domain");

  const {
    tabs, loadTabs, question, exhaustedAndRegenerated, progress,
    analysis, analyzing, loadingQuestion, error,
    submitAnswer, clearAnalysisAndAdvance, activeDomainId,
  } = useSkillPathStore();

  const [answer, setAnswer] = useState("");
  const [runOut, setRunOut] = useState(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (topicId && domainId) {
      // deep-link safety: ensure the store knows the active domain
      useSkillPathStore.setState({ activeDomainId: domainId });
      loadTabs(topicId, domainId);
    }
  }, [topicId, domainId, loadTabs]);

  // fresh editor per question; seed starter code when provided
  useEffect(() => {
    setAnswer(question?.starter_code || "");
    setRunOut(null);
  }, [question?.question_id]);

  const isRunnable =
    question && (question.question_kind === "code" || question.question_kind === "sql");

  const runAnswer = useCallback(async () => {
    if (!isRunnable || !answer.trim()) return;
    setRunning(true);
    try {
      const out = await kernel.run(
        question.question_kind === "sql" ? "sql" : "python", answer);
      setRunOut(out);
    } catch (err) {
      setRunOut({ ok: false, text: `Kernel error: ${err.message}`, image: null });
    } finally {
      setRunning(false);
    }
  }, [isRunnable, answer, question]);

  const submit = useCallback(() => {
    submitAnswer(answer, runOut?.text?.slice(0, 8000) ?? null);
  }, [submitAnswer, answer, runOut]);

  return (
    <div className="mx-auto max-w-3xl p-6">
      <button type="button"
        onClick={() => navigate(`/skillpath/topic/${topicId}/learn?domain=${domainId || activeDomainId}`)}
        className="mb-3 text-xs text-zinc-500 hover:text-zinc-300">
        ← back to Learn
      </button>

      <SubtopicTabs />
      {error && <p className="my-3 text-sm text-red-400">{error}</p>}

      {loadingQuestion && <p className="mt-4 text-sm text-zinc-500">Loading question…</p>}

      {question && (
        <div className="mt-4 space-y-4">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className={`rounded px-2 py-0.5 font-semibold ${DIFF_STYLE[question.difficulty]}`}>
              {question.difficulty}
            </span>
            <span className="text-zinc-500">
              question {question.position} of {question.bank_size}
            </span>
            {question.source === "auto" && (
              <span className="rounded bg-violet-950/60 px-2 py-0.5 text-violet-300">
                fresh — bank grew for you
              </span>
            )}
            {exhaustedAndRegenerated && (
              <span className="text-zinc-500">you cleared the whole bank 🎯</span>
            )}
            {progress && (
              <span className="ml-auto text-zinc-400">
                {progress.correct} correct · {progress.mastery_pct}% to mastery
              </span>
            )}
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
            <p className="whitespace-pre-wrap text-sm leading-6 text-zinc-100">
              {question.question}
            </p>
            <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
              {question.examples.map((ex, i) => (
                <div key={i} className="rounded-md border border-zinc-800 bg-zinc-950/60 p-2 text-xs">
                  <p className="text-zinc-400">Example {i + 1}</p>
                  {ex.input && <p className="mt-1 font-mono text-zinc-300">in: {ex.input}</p>}
                  {ex.output && <p className="font-mono text-zinc-300">out: {ex.output}</p>}
                  {ex.why && <p className="mt-1 text-zinc-500">{ex.why}</p>}
                </div>
              ))}
            </div>
          </div>

          {!analysis && (
            <>
              <CellEditor
                value={answer}
                onChange={setAnswer}
                onRun={isRunnable ? runAnswer : undefined}
                language={question.question_kind === "sql" ? "sql" : "python"}
                minRows={question.question_kind === "text" ? 4 : 8}
                placeholder={question.question_kind === "text"
                  ? "Write your answer…"
                  : "# Your solution — Shift+Enter runs it on your device"}
              />

              {runOut && (
                <pre className={`max-h-48 overflow-auto rounded-md border px-3 py-2 font-mono
                                 text-xs whitespace-pre-wrap
                                 ${runOut.ok === false
                                   ? "border-red-800 bg-red-950/40 text-red-300"
                                   : "border-zinc-800 bg-zinc-950 text-zinc-300"}`}>
                  {runOut.text}
                </pre>
              )}

              <div className="flex gap-2">
                {isRunnable && (
                  <button type="button" onClick={runAnswer} disabled={running || !answer.trim()}
                    className="rounded-lg border border-emerald-700 px-4 py-2 text-sm
                               text-emerald-300 hover:bg-emerald-950/40 disabled:opacity-50">
                    {running ? "Running…" : "▶ Test run"}
                  </button>
                )}
                <button type="button" onClick={submit} disabled={analyzing || !answer.trim()}
                  className="flex-1 rounded-lg bg-sky-600 py-2 text-sm font-semibold
                             text-white hover:bg-sky-500 disabled:bg-zinc-700">
                  {analyzing ? "AI is analyzing your answer…" : "Submit for AI analysis"}
                </button>
              </div>
            </>
          )}

          <AnalysisCard analysis={analysis} onNext={clearAnalysisAndAdvance} />
        </div>
      )}
    </div>
  );
}