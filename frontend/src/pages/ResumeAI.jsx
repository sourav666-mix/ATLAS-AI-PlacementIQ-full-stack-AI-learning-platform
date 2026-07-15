// FILE: frontend/src/pages/ResumeAI.jsx
// BATCH 29 / v10 Resume AI (new) - /resume. Opens with two cards: Analyze My
// Resume and Create My Resume. Analyzer: upload + optional JD -> report ->
// rebuild PDF. Builder: guided form -> AI draft -> editable LivePreview ->
// pick template/pages -> export PDF. Both end in a downloadable PDF; a
// resulting PDF url/base64 is surfaced as a download link.
// REPLACES the Placeholder route target from Batch 24.

import React, { useState } from "react";
import { FileSearch, FilePlus2, ArrowLeft, Download, Upload } from "lucide-react";
import resumeApi from "../api/resumeApi";
import AnalyzerReport from "../components/Resume/AnalyzerReport";
import BuilderForm from "../components/Resume/BuilderForm";
import LivePreview from "../components/Resume/LivePreview";
import TemplatePicker from "../components/Resume/TemplatePicker";
import { Button, Spinner } from "../components/Common";

function DownloadLink({ result }) {
  if (!result) return null;
  const url =
    result.url ||
    result.pdf_url ||
    (result.pdf_base64
      ? `data:application/pdf;base64,${result.pdf_base64}`
      : null);
  if (!url) return null;
  return (
    <a
      href={url}
      download="atlas-resume.pdf"
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 text-sm font-medium transition"
    >
      <Download size={15} /> Download PDF
    </a>
  );
}

export default function ResumeAI() {
  const [mode, setMode] = useState(null); // null | 'analyze' | 'build'

  // Analyzer state
  const [resumeFile, setResumeFile] = useState(null);
  const [jdText, setJdText] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [report, setReport] = useState(null);
  const [rebuilding, setRebuilding] = useState(false);
  const [rebuilt, setRebuilt] = useState(null);

  // Builder state
  const [drafting, setDrafting] = useState(false);
  const [draft, setDraft] = useState(null);
  const [edited, setEdited] = useState(null);
  const [template, setTemplate] = useState("classic");
  const [pages, setPages] = useState(1);
  const [exporting, setExporting] = useState(false);
  const [exported, setExported] = useState(null);

  const [error, setError] = useState(null);

  const runAnalyze = async () => {
    if (!resumeFile) { setError("Upload a resume file first."); return; }
    setAnalyzing(true); setError(null); setReport(null); setRebuilt(null);
    try {
      const data = await resumeApi.analyze({ resumeFile, jdText: jdText.trim() || undefined });
      setReport(data.report || data);
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally {
      setAnalyzing(false);
    }
  };

  const runRebuild = async () => {
    setRebuilding(true); setError(null);
    try {
      const data = await resumeApi.rebuild(report?.analysis_id || report?.id, template);
      setRebuilt(data);
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally {
      setRebuilding(false);
    }
  };

  const runDraft = async (form) => {
    setDrafting(true); setError(null);
    try {
      const data = await resumeApi.builderDraft(form);
      const d = data.draft || data.resume || data;
      setDraft(d); setEdited(d);
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally {
      setDrafting(false);
    }
  };

  const runExport = async () => {
    setExporting(true); setError(null);
    try {
      const data = await resumeApi.builderExport({ draft: edited, template, pages });
      setExported(data);
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally {
      setExporting(false);
    }
  };

  // ---- Entry: two cards ----
  if (!mode) {
    return (
      <div className="p-4 lg:p-6 max-w-4xl mx-auto space-y-6">
        <div className="rise" style={{ "--d": "0ms" }}>
          <h1 className="text-2xl font-bold text-gray-50">Resume AI</h1>
          <p className="text-sm text-gray-500 mt-1">
            Analyze an existing resume against a job, or build a professional one from scratch. Both end in an ATS-safe PDF.
          </p>
        </div>
        <div className="rise grid sm:grid-cols-2 gap-4" style={{ "--d": "80ms" }}>
          <button
            onClick={() => setMode("analyze")}
            className="text-left rounded-2xl border border-gray-800 bg-gray-900 p-6 transition hover:border-cyan-700 hover:-translate-y-0.5"
          >
            <FileSearch size={24} className="text-cyan-400" />
            <p className="mt-3 text-lg font-semibold text-gray-100">Analyze my resume</p>
            <p className="mt-1 text-sm text-gray-500">
              Upload your resume + a JD → ATS score, skill match, STAR rewrites, and the top-3 questions they'll ask.
            </p>
          </button>
          <button
            onClick={() => setMode("build")}
            className="text-left rounded-2xl border border-gray-800 bg-gray-900 p-6 transition hover:border-cyan-700 hover:-translate-y-0.5"
          >
            <FilePlus2 size={24} className="text-emerald-400" />
            <p className="mt-3 text-lg font-semibold text-gray-100">Create my resume</p>
            <p className="mt-1 text-sm text-gray-500">
              Fill a guided form → AI drafts recruiter-grade wording → edit → export a clean 1–2 page PDF.
            </p>
          </button>
        </div>
      </div>
    );
  }

  // ---- Analyzer ----
  if (mode === "analyze") {
    return (
      <div className="p-4 lg:p-6 max-w-3xl mx-auto space-y-5">
        <button onClick={() => setMode(null)} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300">
          <ArrowLeft size={16} /> Resume AI
        </button>
        <h1 className="text-2xl font-bold text-gray-50">Analyze my resume</h1>

        {!report && (
          <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4" style={{ "--d": "0ms" }}>
            <label className="block">
              <span className="text-xs text-gray-400">Resume file (PDF or DOCX)</span>
              <div className="mt-1 flex items-center gap-3">
                <label className="cursor-pointer inline-flex items-center gap-2 rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:border-gray-500">
                  <Upload size={15} /> Choose file
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                    className="hidden"
                  />
                </label>
                {resumeFile && <span className="text-sm text-gray-400 truncate">{resumeFile.name}</span>}
              </div>
            </label>
            <label className="block">
              <span className="text-xs text-gray-400">Job description (optional — enables the smart matcher)</span>
              <textarea
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                rows={4}
                placeholder="Paste the JD to score keyword + semantic match."
                className="mt-1 w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-cyan-700"
              />
            </label>
            {error && <p className="text-sm text-red-400">{error}</p>}
            <Button size="lg" onClick={runAnalyze} disabled={analyzing || !resumeFile}>
              {analyzing ? <Spinner size={16} /> : "Analyze"}
            </Button>
          </div>
        )}

        {report && (
          <>
            <AnalyzerReport report={report} onRebuild={runRebuild} rebuilding={rebuilding} />
            {error && <p className="text-sm text-red-400">{error}</p>}
            {rebuilt && (
              <div className="rise rounded-2xl border border-emerald-900/60 bg-emerald-950/20 p-5 flex items-center justify-between" style={{ "--d": "0ms" }}>
                <p className="text-sm text-emerald-300">Your improved, ATS-optimized resume is ready.</p>
                <DownloadLink result={rebuilt} />
              </div>
            )}
            <button onClick={() => { setReport(null); setRebuilt(null); }} className="text-sm text-gray-500 hover:text-gray-300">
              Analyze another
            </button>
          </>
        )}
      </div>
    );
  }

  // ---- Builder ----
  return (
    <div className="p-4 lg:p-6 max-w-3xl mx-auto space-y-5">
      <button onClick={() => setMode(null)} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300">
        <ArrowLeft size={16} /> Resume AI
      </button>
      <h1 className="text-2xl font-bold text-gray-50">Create my resume</h1>

      {!draft ? (
        <BuilderForm onDraft={runDraft} drafting={drafting} />
      ) : (
        <div className="space-y-5">
          <p className="text-sm text-gray-400">
            Edit any line below, choose a template, then export. Click a field to change it.
          </p>
          <LivePreview draft={draft} onChange={setEdited} />
          <TemplatePicker
            template={template} pages={pages}
            onTemplate={setTemplate} onPages={setPages}
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex items-center gap-3">
            <Button size="lg" onClick={runExport} disabled={exporting}>
              {exporting ? <Spinner size={16} /> : "Export PDF"}
            </Button>
            <DownloadLink result={exported} />
            <button onClick={() => { setDraft(null); setExported(null); }} className="text-sm text-gray-500 hover:text-gray-300">
              Start over
            </button>
          </div>
        </div>
      )}
    </div>
  );
}