// CompanyIntel.jsx - [MOD] Intel Pro + gap map + compare

// FILE: frontend/src/pages/CompanyIntel.jsx
// BATCH 31 / v10 Company Intel (new) - /company. Pick a company -> cached deep
// report (business, packages, tech stack, round-by-round process) + the
// PERSONAL gap map overlaying the company's required skills on the student's
// live radar (green ready / amber practice / red missing), each red item
// linking to the SkillPath topic that fixes it. Compare mode = two side by
// side. REPLACES the Placeholder route target from Batch 24.

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowUpRight, Building2, GitCompare } from "lucide-react";
import companyApi from "../api/companyApi";
import { Badge, Button, Spinner } from "../components/Common";

const GAP_TONE = {
  ready: { dot: "#34d399", label: "Ready", tone: "green" },
  green: { dot: "#34d399", label: "Ready", tone: "green" },
  practice: { dot: "#fbbf24", label: "Practice", tone: "amber" },
  amber: { dot: "#fbbf24", label: "Practice", tone: "amber" },
  missing: { dot: "#f87171", label: "Missing", tone: "red" },
  red: { dot: "#f87171", label: "Missing", tone: "red" },
};

function GapMap({ gap }) {
  const navigate = useNavigate();
  const items = gap?.items || gap?.skills || [];
  if (!items.length) return null;
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-2">
      <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Your gap map</p>
      <p className="text-xs text-gray-500 mb-2">
        This company's required skills, overlaid on your live radar. Red items link to the fix.
      </p>
      {items.map((item, i) => {
        const status = String(item.status || item.level || "practice").toLowerCase();
        const meta = GAP_TONE[status] || GAP_TONE.practice;
        const fixable = status === "missing" || status === "red" || status === "practice" || status === "amber";
        return (
          <button
            key={i}
            onClick={() => item.topic_id && navigate(`/learn/${item.topic_id}`)}
            disabled={!item.topic_id}
            className="w-full flex items-center gap-3 rounded-xl bg-gray-950 border border-gray-800 px-4 py-2.5 text-left hover:border-gray-600 transition group disabled:opacity-80"
          >
            <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ background: meta.dot }} />
            <span className="flex-1 text-sm text-gray-200">{item.skill || item.name || item}</span>
            <Badge tone={meta.tone}>{meta.label}</Badge>
            {fixable && item.topic_id && (
              <ArrowUpRight size={14} className="text-gray-600 group-hover:text-cyan-400" />
            )}
          </button>
        );
      })}
    </div>
  );
}

function Report({ report }) {
  if (!report) return null;
  const rounds = report.interview_process || report.rounds || [];
  return (
    <div className="space-y-4">
      {report.overview && (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500 mb-1">Overview</p>
          <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{report.overview}</p>
        </div>
      )}
      <div className="grid sm:grid-cols-2 gap-3">
        {[
          ["avg_package", "Avg package"],
          ["highest_package", "Highest package"],
          ["hiring_season", "Hiring season"],
          ["cgpa_cutoff", "CGPA cutoff"],
        ].map(([k, label]) =>
          report[k] ? (
            <div key={k} className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
              <p className="text-sm font-semibold text-gray-100">{report[k]}</p>
              <p className="text-[11px] text-gray-500 mt-0.5">{label}</p>
            </div>
          ) : null
        )}
      </div>
      {(report.tech_stack || []).length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500 mb-2">Tech stack</p>
          <div className="flex flex-wrap gap-1.5">
            {report.tech_stack.map((t, i) => <Badge key={i} tone="cyan">{t}</Badge>)}
          </div>
        </div>
      )}
      {rounds.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3">
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Interview process</p>
          {rounds.map((r, i) => (
            <div key={i} className="rounded-xl bg-gray-950 border border-gray-800 p-3">
              <p className="text-sm font-semibold text-gray-200">
                {i + 1}. {r.name || r.round || `Round ${i + 1}`}
              </p>
              {(r.detail || r.description) && (
                <p className="text-xs text-gray-400 mt-1">{r.detail || r.description}</p>
              )}
              {r.strategy && <p className="text-xs text-cyan-400 mt-1">Prep: {r.strategy}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function CompanyIntel() {
  const [companies, setCompanies] = useState(null);
  const [selected, setSelected] = useState(null);
  const [report, setReport] = useState(null);
  const [gap, setGap] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    companyApi.list()
      .then((data) => setCompanies(Array.isArray(data) ? data : data.companies || []))
      .catch(() => setCompanies([]));
  }, []);

  const open = async (company) => {
    setSelected(company);
    setReport(null); setGap(null); setError(null); setLoading(true);
    const slug = company.slug || company.id || company;
    try {
      const [rep, gm] = await Promise.all([
        companyApi.report(slug),
        companyApi.gapMap(slug).catch(() => null),
      ]);
      setReport(rep.report || rep);
      setGap(gm?.gap_map || gm);
    } catch (err) {
      setError(String(err?.response?.data?.detail || "Couldn't load this company's report."));
    } finally {
      setLoading(false);
    }
  };

  if (selected) {
    return (
      <div className="p-4 lg:p-6 max-w-3xl mx-auto space-y-4">
        <button onClick={() => setSelected(null)} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300">
          <ArrowLeft size={16} /> All companies
        </button>
        <h1 className="text-2xl font-bold text-gray-50">{selected.name || selected}</h1>
        {loading ? (
          <div className="py-16 flex justify-center"><Spinner size={28} /></div>
        ) : error ? (
          <p className="text-sm text-red-400">{error}</p>
        ) : (
          <div className="space-y-4">
            <GapMap gap={gap} />
            <Report report={report} />
          </div>
        )}
      </div>
    );
  }

  const list = (companies || []).filter((c) =>
    (c.name || c).toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="p-4 lg:p-6 max-w-3xl mx-auto space-y-5">
      <div className="rise" style={{ "--d": "0ms" }}>
        <h1 className="text-2xl font-bold text-gray-50">Company Intel</h1>
        <p className="text-sm text-gray-500 mt-1">
          Deep company reports with a personal gap map — the exact skills to close before you apply.
        </p>
      </div>
      <div className="rise" style={{ "--d": "60ms" }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search companies…"
          className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-cyan-700"
        />
      </div>

      {!companies ? (
        <div className="py-16 flex justify-center"><Spinner size={28} /></div>
      ) : list.length === 0 ? (
        <p className="text-sm text-gray-500">No companies found. The intel library is seeded by ATLAS AI.</p>
      ) : (
        <div className="rise grid sm:grid-cols-2 gap-3" style={{ "--d": "120ms" }}>
          {list.map((c, i) => (
            <button
              key={c.slug || c.id || i}
              onClick={() => open(c)}
              className="flex items-center gap-3 text-left rounded-2xl border border-gray-800 bg-gray-900 p-4 transition hover:border-gray-600 hover:-translate-y-0.5"
            >
              <span className="h-9 w-9 rounded-lg bg-gray-800 flex items-center justify-center shrink-0">
                <Building2 size={17} className="text-cyan-400" />
              </span>
              <div className="min-w-0">
                <p className="font-semibold text-gray-100 truncate">{c.name || c}</p>
                {c.sector && <p className="text-[11px] text-gray-500 truncate">{c.sector}</p>}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}