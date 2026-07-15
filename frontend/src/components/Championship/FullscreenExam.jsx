// FullscreenExam.jsx - [NEW] proctored 20Q/15min exam
// FILE: frontend/src/components/Championship/FullscreenExam.jsx
// BATCH 30 / v10 Championship (new) - The proctored runner. Renders one
// question at a time (MCQ / rapid quiz / logic), a live countdown derived from
// the SERVER deadline, a question rail, and autosaves each answer. The
// fullscreen guard is wired here: a single grace warning modal, then a hard
// lock that auto-submits. When the server clock passes the deadline, it
// auto-submits too. There is no way to open the assistant from in here.

import React, { useCallback, useEffect, useRef, useState } from "react";
import { AlertTriangle, Clock, ShieldAlert } from "lucide-react";
import useExamStore from "../../store/examStore";
import useFullscreenGuard from "../../hooks/useFullscreenGuard";
import championshipApi from "../../api/championshipApi";
import { Button } from "../Common";

function fmt(ms) {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = String(Math.floor(total / 60)).padStart(2, "0");
  const s = String(total % 60).padStart(2, "0");
  return `${m}:${s}`;
}

export default function FullscreenExam({ onFinished }) {
  const {
    championshipId, title, questions, answers, current,
    deadlineMs, setAnswer, goTo, next, prev, setLocked, setSubmitted,
  } = useExamStore();

  const [remaining, setRemaining] = useState(
    deadlineMs ? deadlineMs - Date.now() : 0
  );
  const [warning, setWarning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const submittedRef = useRef(false);

  const doSubmit = useCallback(
    async (reason = "manual") => {
      if (submittedRef.current) return;
      submittedRef.current = true;
      setSubmitting(true);
      try {
        const result = await championshipApi.submit(championshipId, answers, {
          reason,
          time_used_secs: deadlineMs
            ? Math.floor((900000 - (deadlineMs - Date.now())) / 1000)
            : undefined,
        });
        setSubmitted(result);
      } catch (_) {
        setSubmitted(null);
      } finally {
        setSubmitting(false);
        if (onFinished) onFinished();
      }
    },
    [championshipId, answers, deadlineMs, setSubmitted, onFinished]
  );

  // Proctor guard: warn once, then lock + submit.
  const { requestFullscreen } = useFullscreenGuard({
    active: !submittedRef.current,
    onWarn: () => setWarning(true),
    onLock: () => {
      setLocked(true);
      championshipApi.violation(championshipId, "fullscreen_exit");
      doSubmit("locked");
    },
  });

  // Request fullscreen on mount.
  useEffect(() => {
    requestFullscreen();
  }, [requestFullscreen]);

  // Server-deadline countdown.
  useEffect(() => {
    if (!deadlineMs) return undefined;
    const tick = setInterval(() => {
      const left = deadlineMs - Date.now();
      setRemaining(left);
      if (left <= 0) {
        clearInterval(tick);
        doSubmit("time");
      }
    }, 500);
    return () => clearInterval(tick);
  }, [deadlineMs, doSubmit]);

  const q = questions[current] || {};
  const options = q.options || q.choices || [];
  const answered = Object.keys(answers).length;

  const choose = (value) => {
    setAnswer(current, value);
    championshipApi.answer(championshipId, current, value); // best-effort autosave
  };

  const low = remaining < 60000;

  return (
    <div className="fixed inset-0 z-50 bg-gray-950 text-gray-100 flex flex-col">
      {/* Top bar */}
      <div className="h-14 shrink-0 border-b border-gray-800 flex items-center justify-between px-5">
        <div className="flex items-center gap-2">
          <ShieldAlert size={16} className="text-amber-400" />
          <span className="text-sm font-semibold truncate max-w-[40vw]">{title}</span>
        </div>
        <div className={`flex items-center gap-2 font-bold tabular-nums ${low ? "text-red-400 animate-pulse" : "text-gray-100"}`}>
          <Clock size={16} /> {fmt(remaining)}
        </div>
      </div>

      <div className="flex-1 flex min-h-0">
        {/* Question rail */}
        <aside className="w-16 sm:w-20 shrink-0 border-r border-gray-800 overflow-y-auto p-2">
          <div className="grid grid-cols-2 gap-1.5">
            {questions.map((_, i) => {
              const done = answers[i] != null && answers[i] !== "";
              const active = i === current;
              return (
                <button
                  key={i}
                  onClick={() => goTo(i)}
                  className={`h-8 rounded-lg text-xs font-semibold transition ${
                    active
                      ? "bg-cyan-600 text-white"
                      : done
                      ? "bg-emerald-950 text-emerald-300 border border-emerald-900"
                      : "bg-gray-900 text-gray-500 border border-gray-800"
                  }`}
                >
                  {i + 1}
                </button>
              );
            })}
          </div>
        </aside>

        {/* Question body */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-10">
          <div className="max-w-2xl mx-auto space-y-6">
            <p className="text-xs text-gray-500">
              Question {current + 1} of {questions.length}
              {q.type && <span className="ml-2 uppercase tracking-wide">{q.type}</span>}
            </p>
            <h2 className="text-lg text-gray-100 leading-relaxed whitespace-pre-wrap">
              {q.question || q.question_text || q.prompt}
            </h2>

            {options.length > 0 ? (
              <div className="space-y-2">
                {options.map((opt, i) => {
                  const value = typeof opt === "string" ? opt : opt.value ?? opt.text;
                  const label = typeof opt === "string" ? opt : opt.text ?? opt.value;
                  const selected = answers[current] === value;
                  return (
                    <button
                      key={i}
                      onClick={() => choose(value)}
                      className={`w-full text-left rounded-xl border px-4 py-3 text-sm transition ${
                        selected
                          ? "border-cyan-600 bg-cyan-950/40 text-cyan-100"
                          : "border-gray-800 bg-gray-900 text-gray-300 hover:border-gray-600"
                      }`}
                    >
                      <span className="text-gray-500 mr-2">{String.fromCharCode(65 + i)}.</span>
                      {label}
                    </button>
                  );
                })}
              </div>
            ) : (
              <input
                value={answers[current] || ""}
                onChange={(e) => choose(e.target.value)}
                placeholder="Type your answer"
                className="w-full bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-cyan-700"
              />
            )}

            <div className="flex items-center justify-between pt-4">
              <Button variant="ghost" onClick={prev} disabled={current === 0}>
                Previous
              </Button>
              {current < questions.length - 1 ? (
                <Button onClick={next}>Next</Button>
              ) : (
                <Button
                  variant="success"
                  onClick={() => doSubmit("manual")}
                  disabled={submitting}
                >
                  {submitting ? "Submitting…" : "Submit exam"}
                </Button>
              )}
            </div>
            <p className="text-center text-xs text-gray-600">
              {answered}/{questions.length} answered · your paper autosaves as you go
            </p>
          </div>
        </main>
      </div>

      {/* One-time grace warning */}
      {warning && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 p-4">
          <div className="bg-gray-900 border border-amber-700 rounded-2xl p-6 max-w-sm text-center">
            <AlertTriangle size={28} className="text-amber-400 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-gray-100">Stay in full-screen</h3>
            <p className="text-sm text-gray-400 mt-2">
              That's your one warning. Leaving full-screen or switching tabs
              again will lock and submit your exam immediately.
            </p>
            <Button full className="mt-4" onClick={() => { setWarning(false); requestFullscreen(); }}>
              Return to exam
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}