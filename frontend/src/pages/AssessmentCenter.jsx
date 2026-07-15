// AssessmentCenter.jsx - [NEW] Mock Interview | Aptitude | Analytics
// FILE: frontend/src/pages/AssessmentCenter.jsx
// BATCH 31 / v10 Assessment Center (new) - /assessment. Three tabs:
//   Mock Interview (text): role + company + level -> Q set -> per-answer score
//   Aptitude: category / company preset -> timed set -> per-option explanations
//   My Analytics: lifetime solved, accuracy trend, weakest subtopics -> drill
// A shared QuestionSet runner handles both quiz-style flows.
// REPLACES the Placeholder route target from Batch 24.

import React, { useEffect, useState } from "react";
import { MessageSquare, Calculator, LineChart as LineIcon, ArrowLeft } from "lucide-react";
import assessmentApi from "../api/assessmentApi";
import LineChart from "../components/Charts/LineChart";
import { Badge, Button, Spinner } from "../components/Common";

const APT_CATEGORIES = ["Quantitative", "Logical", "Verbal", "Data Interpretation"];
const APT_PRESETS = ["General", "TCS NQT", "Infosys", "Wipro", "Accenture"];
const LEVELS = ["Beginner", "Intermediate", "Advanced"];

function normalizeQuestions(data) {
  const list = data.questions || data.question_set || data.items || [];
  return list.map((q, i) => ({
    id: q.id ?? i,
    text: q.question || q.question_text || q.prompt,
    options: q.options || q.choices || [],
    type: q.type,
  }));
}

// Shared runner: renders a set, collects answers, submits, shows the graded
// review with per-option explanations (aptitude) or per-answer scores (mock).
function QuestionSet({ title, sessionId, questions, onSubmit, onBack }) {
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    setSubmitting(true);
    try {
      // Backends expect an ordered list per question (aptitude: selected
      // option index, -1 if unanswered; mock: the raw text answer) — not the
      // {questionId: value} map we collect answers into while rendering.
      const ordered = questions.map((q) => {
        const raw = answers[q.id];
        if (q.options.length > 0) {
          return q.options.findIndex((opt) => {
            const v = typeof opt === "string" ? opt : opt.value ?? opt.text;
            return v === raw;
          });
        }
        return raw ?? "";
      });
      const data = await onSubmit(sessionId, ordered);
      setResult(data);
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    const reviewed = result.review || result.questions || questions;
    const score = Math.round(Number(result.score ?? 0));
    const total = Number(result.total ?? questions.length);
    return (
      <div className="space-y-4">
        <div className="rounded-2xl border border-gray-800 bg-gray-900 p-5">
          <p className="text-2xl font-bold text-gray-50 tabular-nums">
            {score}<span className="text-sm text-gray-500 font-medium"> / {total}</span>
          </p>
          {result.points_awarded != null && <Badge tone="green">+{result.points_awarded} points</Badge>}
        </div>
        {reviewed.map((q, i) => (
          <div key={i} className="rounded-2xl border border-gray-800 bg-gray-900 p-5 space-y-2">
            <p className="text-sm text-gray-100">{i + 1}. {q.text || q.question}</p>
            {q.score != null && (
              <p className={`text-xs font-bold ${q.score >= 7 ? "text-emerald-400" : q.score >= 4 ? "text-amber-400" : "text-red-400"}`}>
                Score {q.score}/10
              </p>
            )}
            {q.correct_option != null && (
              <p className="text-xs text-emerald-400">Correct: {q.correct_option}</p>
            )}
            {q.explanations &&
              Object.entries(q.explanations).map(([opt, why]) => (
                <p key={opt} className="text-xs text-gray-400">
                  <span className="text-gray-300">{opt}:</span> {why}
                </p>
              ))}
            {q.explanation && <p className="text-xs text-gray-400">{q.explanation}</p>}
            {q.model_hint && <p className="text-xs text-gray-400">Model: {q.model_hint}</p>}
          </div>
        ))}
        <Button onClick={onBack}>Done</Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <button onClick={onBack} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300">
        <ArrowLeft size={16} /> {title}
      </button>
      {questions.map((q, i) => (
        <div key={q.id} className="rounded-2xl border border-gray-800 bg-gray-900 p-5 space-y-3">
          <p className="text-sm text-gray-100">{i + 1}. {q.text}</p>
          {q.options.length > 0 ? (
            <div className="space-y-2">
              {q.options.map((opt, oi) => {
                const value = typeof opt === "string" ? opt : opt.value ?? opt.text;
                const label = typeof opt === "string" ? opt : opt.text ?? opt.value;
                const selected = answers[q.id] === value;
                return (
                  <button
                    key={oi}
                    onClick={() => setAnswers((a) => ({ ...a, [q.id]: value }))}
                    className={`w-full text-left rounded-xl border px-4 py-2.5 text-sm transition ${
                      selected ? "border-cyan-600 bg-cyan-950/40 text-cyan-100" : "border-gray-800 bg-gray-950 text-gray-300 hover:border-gray-600"
                    }`}
                  >
                    <span className="text-gray-500 mr-2">{String.fromCharCode(65 + oi)}.</span>{label}
                  </button>
                );
              })}
            </div>
          ) : (
            <textarea
              value={answers[q.id] || ""}
              onChange={(e) => setAnswers((a) => ({ ...a, [q.id]: e.target.value }))}
              rows={3}
              placeholder="Your answer"
              className="w-full bg-gray-950 border border-gray-800 rounded-xl px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-cyan-700"
            />
          )}
        </div>
      ))}
      <Button size="lg" onClick={submit} disabled={submitting}>
        {submitting ? <Spinner size={16} /> : "Submit for scoring"}
      </Button>
    </div>
  );
}

export default function AssessmentCenter() {
  const [tab, setTab] = useState("mock");
  const [runner, setRunner] = useState(null); // {kind, title, sessionId, questions}
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);

  // Mock config
  const [role, setRole] = useState("");
  const [company, setCompany] = useState("");
  const [level, setLevel] = useState("Intermediate");

  // Aptitude config
  const [category, setCategory] = useState("Quantitative");
  const [preset, setPreset] = useState("General");

  // Analytics
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    if (tab === "analytics" && !analytics) {
      assessmentApi.analytics().then(setAnalytics).catch(() => setAnalytics({}));
    }
  }, [tab, analytics]);

  const startMock = async () => {
    setStarting(true); setError(null);
    try {
      const data = await assessmentApi.startMock({ role, company, level });
      setRunner({
        kind: "mock",
        title: "Mock Interview",
        sessionId: data.session_id || data.id,
        questions: normalizeQuestions(data),
      });
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally { setStarting(false); }
  };

  const startAptitude = async () => {
    setStarting(true); setError(null);
    try {
      const data = await assessmentApi.startAptitude({ category, preset });
      setRunner({
        kind: "aptitude",
        title: "Aptitude",
        sessionId: data.session_id || data.id,
        questions: normalizeQuestions(data),
      });
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally { setStarting(false); }
  };

  if (runner) {
    return (
      <div className="p-4 lg:p-6 max-w-2xl mx-auto">
        <QuestionSet
          title={`${runner.title} setup`}
          sessionId={runner.sessionId}
          questions={runner.questions}
          onSubmit={runner.kind === "mock" ? assessmentApi.submitMock : assessmentApi.submitAptitude}
          onBack={() => setRunner(null)}
        />
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-6 max-w-3xl mx-auto space-y-5">
      <div className="rise" style={{ "--d": "0ms" }}>
        <h1 className="text-2xl font-bold text-gray-50">Assessment Center</h1>
        <p className="text-sm text-gray-500 mt-1">
          Mock interviews and aptitude in one place — recruiters test both.
        </p>
      </div>

      <div className="rise flex gap-1 border-b border-gray-800" style={{ "--d": "60ms" }}>
        {[
          { id: "mock", label: "Mock Interview", icon: MessageSquare },
          { id: "aptitude", label: "Aptitude", icon: Calculator },
          { id: "analytics", label: "My Analytics", icon: LineIcon },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`px-4 py-2 text-sm border-b-2 -mb-px transition ${
              tab === id ? "border-cyan-500 text-cyan-300" : "border-transparent text-gray-500 hover:text-gray-300"
            }`}
          >
            <Icon size={14} className="inline mr-1.5" /> {label}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {tab === "mock" && (
        <div className="rise space-y-4" style={{ "--d": "120ms" }}>
          <div className="grid sm:grid-cols-2 gap-3">
            <label className="block">
              <span className="text-xs text-gray-400">Target role</span>
              <input value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. Data Analyst"
                className="mt-1 w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-cyan-700" />
            </label>
            <label className="block">
              <span className="text-xs text-gray-400">Target company (optional)</span>
              <input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="e.g. TCS"
                className="mt-1 w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-cyan-700" />
            </label>
          </div>
          <div className="flex gap-2">
            {LEVELS.map((l) => (
              <button key={l} onClick={() => setLevel(l)}
                className={`px-4 py-2 rounded-xl border text-sm transition ${level === l ? "border-cyan-600 bg-cyan-950/30 text-cyan-200" : "border-gray-800 bg-gray-900 text-gray-300 hover:border-gray-600"}`}>
                {l}
              </button>
            ))}
          </div>
          <Button size="lg" onClick={startMock} disabled={starting || !role}>
            {starting ? <Spinner size={16} /> : "Start mock interview"}
          </Button>
          <p className="text-xs text-gray-600">Text-based, 5–10 questions mixing technical, DSA-verbal, HR, and system design. For live voice, use Interview Studio.</p>
        </div>
      )}

      {tab === "aptitude" && (
        <div className="rise space-y-4" style={{ "--d": "120ms" }}>
          <div>
            <p className="text-sm font-semibold text-gray-300 mb-2">Category</p>
            <div className="grid grid-cols-2 gap-2">
              {APT_CATEGORIES.map((c) => (
                <button key={c} onClick={() => setCategory(c)}
                  className={`rounded-xl border px-4 py-2.5 text-sm transition ${category === c ? "border-cyan-600 bg-cyan-950/30 text-cyan-200" : "border-gray-800 bg-gray-900 text-gray-300 hover:border-gray-600"}`}>
                  {c}
                </button>
              ))}
            </div>
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-300 mb-2">Company preset</p>
            <div className="flex flex-wrap gap-2">
              {APT_PRESETS.map((p) => (
                <button key={p} onClick={() => setPreset(p)}
                  className={`px-3 py-1.5 rounded-lg text-xs transition ${preset === p ? "bg-gray-800 text-gray-100" : "text-gray-500 hover:text-gray-300"}`}>
                  {p}
                </button>
              ))}
            </div>
          </div>
          <Button size="lg" onClick={startAptitude} disabled={starting}>
            {starting ? <Spinner size={16} /> : "Start aptitude set"}
          </Button>
        </div>
      )}

      {tab === "analytics" && (
        <div className="rise space-y-4" style={{ "--d": "120ms" }}>
          {!analytics ? (
            <div className="py-12 flex justify-center"><Spinner /></div>
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {[
                  ["aptitude_solved", "Aptitude solved"],
                  ["mock_sessions", "Mock interviews"],
                  ["avg_accuracy", "Avg accuracy %"],
                ].map(([k, label]) => (
                  <div key={k} className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
                    <p className="text-2xl font-bold text-gray-50 tabular-nums">
                      {Math.round(Number(analytics[k] ?? 0))}
                    </p>
                    <p className="text-[11px] text-gray-500 mt-1">{label}</p>
                  </div>
                ))}
              </div>
              {(analytics.accuracy_trend || []).length > 0 && (
                <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
                  <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500 mb-2">Accuracy trend</p>
                  <LineChart data={(analytics.accuracy_trend || []).map((v, i) => ({
                    label: v.label || `#${i + 1}`, value: Number(v.value ?? v.accuracy ?? v),
                  }))} />
                </div>
              )}
              {(analytics.weakest_subtopics || []).length > 0 && (
                <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-2">
                  <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Weakest sub-topics</p>
                  {(analytics.weakest_subtopics || []).map((w, i) => (
                    <div key={i} className="flex items-center justify-between rounded-xl bg-gray-950 border border-gray-800 px-4 py-2.5">
                      <span className="text-sm text-gray-300">{w.name || w.topic || w}</span>
                      <span className="text-xs text-amber-400 tabular-nums">{Math.round(w.accuracy ?? 0)}%</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}