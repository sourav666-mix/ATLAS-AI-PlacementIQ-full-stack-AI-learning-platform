// Profile.jsx - [NEW] solve counts, resumes, subscription, badges
// FILE: frontend/src/pages/Profile.jsx
// BATCH 31 / v10 Profile (new) - /profile. The student's identity + lifetime
// stat counters ("412 aptitude questions solved | 23 mock interviews"), the
// skill radar, and their generated resume documents. Reads the dashboard +
// analytics + resume documents that already exist. REPLACES the Placeholder.

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogOut, FileText, Download, User as UserIcon } from "lucide-react";
import useAuthStore from "../store/authStore";
import useProfileStore from "../store/profileStore";
import assessmentApi from "../api/assessmentApi";
import resumeApi from "../api/resumeApi";
import RadarChart from "../components/Charts/RadarChart";
import { Button, Spinner } from "../components/Common";

export default function Profile() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { radar, profileBar, streak, load } = useProfileStore();
  const [analytics, setAnalytics] = useState(null);
  const [docs, setDocs] = useState(null);

  useEffect(() => {
    load();
    assessmentApi.analytics().then(setAnalytics).catch(() => setAnalytics({}));
    resumeApi.documents()
      .then((d) => setDocs(Array.isArray(d) ? d : d.documents || []))
      .catch(() => setDocs([]));
  }, [load]);

  const doLogout = () => { logout(); navigate("/login"); };

  const stats = [
    ["Aptitude solved", analytics?.aptitude_solved],
    ["Mock interviews", analytics?.mock_sessions],
    ["Profile score", profileBar?.score],
    ["Day streak", streak?.days],
  ];

  return (
    <div className="p-4 lg:p-6 max-w-3xl mx-auto space-y-5">
      {/* Identity */}
      <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5 flex items-center gap-4" style={{ "--d": "0ms" }}>
        <span className="h-16 w-16 rounded-full bg-cyan-950 text-cyan-300 flex items-center justify-center shrink-0">
          <UserIcon size={28} />
        </span>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-bold text-gray-50 truncate">
            {user?.full_name || "Student"}
          </h1>
          <p className="text-sm text-gray-500 truncate">{user?.email}</p>
          {user?.college_name && (
            <p className="text-xs text-gray-600 mt-0.5">{user.college_name}</p>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={doLogout}>
          <LogOut size={14} className="inline mr-1" /> Log out
        </Button>
      </div>

      {/* Lifetime stats */}
      <div className="rise grid grid-cols-2 sm:grid-cols-4 gap-3" style={{ "--d": "80ms" }}>
        {stats.map(([label, value]) => (
          <div key={label} className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
            <p className="text-2xl font-bold text-gray-50 tabular-nums">
              {value != null ? Math.round(Number(value)) : "—"}
            </p>
            <p className="text-[11px] text-gray-500 mt-1">{label}</p>
          </div>
        ))}
      </div>

      {/* Radar */}
      {radar.length >= 3 && (
        <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5" style={{ "--d": "140ms" }}>
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500 mb-1">Skill radar</p>
          <RadarChart data={radar} />
        </div>
      )}

      {/* Resume documents */}
      <div className="rise bg-gray-900 border border-gray-800 rounded-2xl p-5" style={{ "--d": "200ms" }}>
        <div className="flex items-center justify-between mb-3">
          <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">Your resumes</p>
          <Button size="sm" variant="ghost" onClick={() => navigate("/resume")}>
            <FileText size={13} className="inline mr-1" /> New
          </Button>
        </div>
        {docs == null ? (
          <div className="py-6 flex justify-center"><Spinner /></div>
        ) : docs.length === 0 ? (
          <p className="text-sm text-gray-500">No resumes yet. Build or analyze one in Resume AI.</p>
        ) : (
          <div className="space-y-2">
            {docs.map((d, i) => (
              <div key={d.id || i} className="flex items-center justify-between rounded-xl bg-gray-950 border border-gray-800 px-4 py-3">
                <div className="min-w-0">
                  <p className="text-sm text-gray-200 truncate">
                    {d.mode === "analyzed" ? "Analyzed resume" : "Built resume"}
                    {d.template && <span className="text-gray-500"> · {d.template}</span>}
                  </p>
                  {d.created_at && <p className="text-[11px] text-gray-600">{d.created_at}</p>}
                </div>
                {(d.pdf_url || d.url) && (
                  <a href={d.pdf_url || d.url} target="_blank" rel="noreferrer"
                    className="inline-flex items-center gap-1.5 text-sm text-cyan-400 hover:text-cyan-300">
                    <Download size={14} /> PDF
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}