// JobsBoard.jsx - [NEW] verified openings + match + tracker
// FILE: frontend/src/pages/JobsBoard.jsx
// BATCH 29 / v10 Jobs Board (new) - /jobs. Two tabs: Browse (verified
// postings with personal match scores, filterable) and Tracker (the kanban
// pipeline of saved jobs). Save + advance stage are optimistic. Students have
// NO posting path anywhere here. REPLACES the Placeholder route from Batch 24.

import React, { useEffect, useState } from "react";
import { Briefcase, LayoutGrid } from "lucide-react";
import jobsApi from "../api/jobsApi";
import JobCard from "../components/Jobs/JobCard";
import TrackerBoard from "../components/Jobs/TrackerBoard";
import { Spinner } from "../components/Common";

const TYPES = [
  { id: "", label: "All" },
  { id: "job", label: "Jobs" },
  { id: "internship", label: "Internships" },
];

export default function JobsBoard() {
  const [tab, setTab] = useState("browse");
  const [type, setType] = useState("");
  const [minMatch, setMinMatch] = useState(0);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(null);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true); setError(null);
    try {
      const params = {};
      if (type) params.type = type;
      if (minMatch) params.min_match = minMatch;
      const data = await jobsApi.list(params);
      const list = Array.isArray(data) ? data : data.jobs || data.postings || [];
      setJobs(list.map((j) => ({ ...j, id: j.id })));
    } catch (err) {
      setError(
        String(
          err?.response?.data?.detail ||
            "Couldn't load postings. Make sure the jobs board is seeded."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [type, minMatch]);

  const save = async (job) => {
    setSaving(job.id);
    // optimistic
    setJobs((prev) => prev.map((j) => (j.id === job.id ? { ...j, saved: !j.saved, stage: j.stage || "saved" } : j)));
    try {
      await jobsApi.save(job.id);
    } catch (_) {
      setJobs((prev) => prev.map((j) => (j.id === job.id ? { ...j, saved: job.saved } : j)));
    } finally {
      setSaving(null);
    }
  };

  const setStatus = async (job, stage) => {
    setJobs((prev) => prev.map((j) => (j.id === job.id ? { ...j, stage } : j)));
    try {
      await jobsApi.setStatus(job.id, stage);
    } catch (_) {
      /* revert silently is noisy; leave optimistic value */
    }
  };

  const saved = jobs.filter((j) => j.saved);

  return (
    <div className="p-4 lg:p-6 max-w-4xl mx-auto space-y-5">
      <div className="rise flex items-center justify-between" style={{ "--d": "0ms" }}>
        <div>
          <h1 className="text-2xl font-bold text-gray-50">Jobs Board</h1>
          <p className="text-sm text-gray-500 mt-1">
            Verified openings with a personal match score. Save and track them through to an offer.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="rise flex gap-1 border-b border-gray-800" style={{ "--d": "60ms" }}>
        <button
          onClick={() => setTab("browse")}
          className={`px-4 py-2 text-sm border-b-2 -mb-px transition ${
            tab === "browse" ? "border-cyan-500 text-cyan-300" : "border-transparent text-gray-500 hover:text-gray-300"
          }`}
        >
          <Briefcase size={14} className="inline mr-1.5" /> Browse
        </button>
        <button
          onClick={() => setTab("tracker")}
          className={`px-4 py-2 text-sm border-b-2 -mb-px transition ${
            tab === "tracker" ? "border-cyan-500 text-cyan-300" : "border-transparent text-gray-500 hover:text-gray-300"
          }`}
        >
          <LayoutGrid size={14} className="inline mr-1.5" /> Tracker
          {saved.length > 0 && <span className="ml-1.5 text-xs text-gray-600">{saved.length}</span>}
        </button>
      </div>

      {tab === "browse" ? (
        <>
          {/* Filters */}
          <div className="rise flex flex-wrap items-center gap-3" style={{ "--d": "120ms" }}>
            <div className="flex gap-1">
              {TYPES.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setType(t.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs transition ${
                    type === t.id ? "bg-gray-800 text-gray-100" : "text-gray-500 hover:text-gray-300"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
            <label className="flex items-center gap-2 text-xs text-gray-500">
              Min match
              <select
                value={minMatch}
                onChange={(e) => setMinMatch(Number(e.target.value))}
                className="bg-gray-950 border border-gray-800 rounded-lg px-2 py-1 text-gray-300 focus:outline-none focus:border-cyan-700"
              >
                {[0, 60, 70, 80].map((v) => (
                  <option key={v} value={v}>{v === 0 ? "Any" : `${v}%+`}</option>
                ))}
              </select>
            </label>
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          {loading ? (
            <div className="py-16 flex justify-center"><Spinner size={28} /></div>
          ) : jobs.length === 0 ? (
            <p className="text-sm text-gray-500">No postings match these filters right now.</p>
          ) : (
            <div className="rise space-y-3" style={{ "--d": "180ms" }}>
              {jobs.map((job) => (
                <JobCard
                  key={job.id}
                  job={job}
                  onSave={save}
                  onStatus={setStatus}
                  saving={saving === job.id}
                />
              ))}
            </div>
          )}
        </>
      ) : (
        <div className="rise" style={{ "--d": "120ms" }}>
          <TrackerBoard jobs={saved} onOpen={() => setTab("browse")} />
        </div>
      )}
    </div>
  );
}