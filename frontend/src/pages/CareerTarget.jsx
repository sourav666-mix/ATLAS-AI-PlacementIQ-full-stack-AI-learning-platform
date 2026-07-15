/**
 * ATLAS AI v12 — Career Target & Gap Engine page.
 * Three steps: (1) build profile, (2) see readiness + per-company gap %,
 * (3) generate the one-time 12-week plan. Everything routes back into ATLAS.
 */
import React, { useEffect, useState } from "react";
import useCareerStore from "../store/careerStore";
import LeetCodeInput from "../components/Career/LeetCodeInput";
import SkillsEditor from "../components/Career/SkillsEditor";
import ProjectsEditor from "../components/Career/ProjectsEditor";
import CompanyPicker from "../components/Career/CompanyPicker";
import GapRadar from "../components/Career/GapRadar";
import GapScoreCards from "../components/Career/GapScoreCards";
import PlanTimeline from "../components/Career/PlanTimeline";

const DOMAINS = [
  ["data_science", "Data Science"],
  ["data_analysis", "Data Analysis"],
  ["artificial_intelligence", "Artificial Intelligence"],
  ["generative_ai", "Generative AI"],
  ["frontend", "Frontend"],
  ["backend", "Backend"],
  ["cloud", "Cloud / DevOps"],
  ["mlops", "MLOps"],
  ["cybersecurity", "Cybersecurity"],
];

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-400">{label}</span>
      {children}
    </label>
  );
}

const inputCls =
  "w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-600 outline-none focus:border-emerald-500";

export default function CareerTarget() {
  const s = useCareerStore();
  const { profile, setField, loadCompanies, saveProfile, analyze, parseResume } = s;
  const [step, setStep] = useState(1);
  const [detected, setDetected] = useState([]);

  useEffect(() => {
    s.hydrateFromServer();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (profile.target_domain) loadCompanies(profile.target_domain);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile.target_domain]);

  const onResume = async (e) => {
    const file = e.target.files?.[0];
    if (file) setDetected(await parseResume(file));
  };

  const onSave = async () => {
    try {
      await saveProfile();
      setStep(2);
    } catch {
      /* error surfaced from store */
    }
  };

  const onAnalyze = async () => {
    try {
      await analyze(false);
      setStep(3);
    } catch {
      /* error surfaced from store */
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-white">Career Target &amp; Gap Engine</h1>
        <p className="text-sm text-slate-400">
          Am I ready? What do I fix? Pick your target companies and find out — then close
          the gap without leaving ATLAS.
        </p>
      </header>

      {/* step indicator */}
      <div className="mb-6 flex items-center gap-2 text-xs">
        {["Profile", "Readiness", "Plan"].map((t, i) => (
          <React.Fragment key={t}>
            <button
              type="button"
              onClick={() => (i + 1 <= step ? setStep(i + 1) : null)}
              className={`rounded-full px-3 py-1 font-medium transition ${
                step === i + 1
                  ? "bg-emerald-600 text-white"
                  : step > i + 1
                  ? "bg-slate-700 text-slate-300"
                  : "bg-slate-900 text-slate-600"
              }`}
            >
              {i + 1}. {t}
            </button>
            {i < 2 && <span className="text-slate-700">—</span>}
          </React.Fragment>
        ))}
      </div>

      {s.error && (
        <div className="mb-4 rounded-lg border border-rose-800 bg-rose-950/40 px-4 py-2 text-sm text-rose-300">
          {s.error}
        </div>
      )}

      {step === 1 && (
        <div className="space-y-5">
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
            <h3 className="mb-3 text-sm font-semibold text-white">About You</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Full name">
                <input
                  className={inputCls}
                  value={profile.full_name}
                  onChange={(e) => setField("full_name", e.target.value)}
                  placeholder="Rahul Sharma"
                />
              </Field>
              <Field label="Branch">
                <input
                  className={inputCls}
                  value={profile.branch}
                  onChange={(e) => setField("branch", e.target.value)}
                  placeholder="CSE"
                />
              </Field>
              <Field label="Specialization">
                <input
                  className={inputCls}
                  value={profile.specialization}
                  onChange={(e) => setField("specialization", e.target.value)}
                  placeholder="AI & ML / Core CSE"
                />
              </Field>
              <Field label="CGPA">
                <input
                  className={inputCls}
                  type="number"
                  step="0.01"
                  value={profile.cgpa}
                  onChange={(e) => setField("cgpa", e.target.value)}
                  placeholder="7.8"
                />
              </Field>
              <Field label="Target domain">
                <select
                  className={inputCls}
                  value={profile.target_domain}
                  onChange={(e) => setField("target_domain", e.target.value)}
                >
                  {DOMAINS.map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
              </Field>
              <Field label="SQL / MySQL level">
                <select
                  className={inputCls}
                  value={profile.sql_level}
                  onChange={(e) => setField("sql_level", e.target.value)}
                >
                  {["none", "basic", "intermediate", "advanced"].map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </select>
              </Field>
            </div>
            <div className="mt-3">
              <Field label="What SQL can you actually do? (joins, group by, window functions…)">
                <input
                  className={inputCls}
                  value={profile.sql_details}
                  onChange={(e) => setField("sql_details", e.target.value)}
                  placeholder="joins, group by, subqueries"
                />
              </Field>
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <label className="cursor-pointer rounded-lg border border-dashed border-slate-600 px-4 py-2 text-xs text-slate-300 hover:border-emerald-500">
                {s.parsingResume
                  ? "Reading resume…"
                  : profile.resume_filename || "Upload resume (PDF/DOCX) — optional"}
                <input type="file" accept=".pdf,.docx,.txt" onChange={onResume} hidden />
              </label>
              {detected.length > 0 && (
                <span className="text-[11px] text-emerald-400">
                  Found {detected.length} skills in your resume — add the ones that fit below.
                </span>
              )}
            </div>
          </div>

          <LeetCodeInput />
          <SkillsEditor />
          <ProjectsEditor />
          <CompanyPicker />

          <button
            type="button"
            disabled={s.saving || profile.targets.length === 0}
            onClick={onSave}
            className="w-full rounded-xl bg-emerald-600 py-3 font-semibold text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {s.saving ? "Scoring your profile…" : "See my readiness →"}
          </button>
        </div>
      )}

      {step === 2 && s.result && (
        <div className="space-y-5">
          <GapScoreCards result={s.result} />
          <GapRadar pillars={s.result.pillars} targets={s.result.targets} />

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="rounded-xl border border-slate-700 px-5 py-3 text-sm font-medium text-slate-300 hover:border-slate-500"
            >
              ← Edit profile
            </button>
            <button
              type="button"
              disabled={s.analyzing}
              onClick={onAnalyze}
              className="flex-1 rounded-xl bg-emerald-600 py-3 font-semibold text-white transition hover:bg-emerald-500 disabled:opacity-40"
            >
              {s.analyzing ? "Building your 12-week plan…" : "Generate my learning plan →"}
            </button>
          </div>
        </div>
      )}

      {step === 3 && s.report && (
        <div className="space-y-5">
          <PlanTimeline report={s.report} />
          <button
            type="button"
            onClick={() => setStep(2)}
            className="rounded-xl border border-slate-700 px-5 py-3 text-sm font-medium text-slate-300 hover:border-slate-500"
          >
            ← Back to readiness
          </button>
        </div>
      )}
    </div>
  );
}