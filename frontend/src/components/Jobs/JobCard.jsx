// JobCard.jsx - [NEW] verified posting card
// FILE: frontend/src/components/Jobs/JobCard.jsx
// BATCH 29 / v10 Jobs Board (new) - One verified posting: role, company,
// type, location, stipend/CTC, required skills, deadline, trust badge, and
// the personal match. Below 60% match, surfaces "close the gap" -> SkillPath.
// One-click "Tailor resume" -> Resume Analyzer with the JD; "Prep" ->
// Company Intel. Students can save + advance the tracker; they never post.

import React from "react";
import { useNavigate } from "react-router-dom";
import { MapPin, Building2, Clock, Bookmark, BookmarkCheck, FileText } from "lucide-react";
import MatchBadge from "./MatchBadge";
import { Badge, Button } from "../Common";

const STAGES = ["saved", "applied", "test", "interview", "offer"];

export default function JobCard({ job, onSave, onStatus, saving }) {
  const navigate = useNavigate();
  const gaps = job.gap_topics || job.missing_topics || [];
  const lowMatch = job.match_score != null && job.match_score < 60;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <div className="flex items-start gap-4">
        <MatchBadge score={job.match_score} />
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="font-semibold text-gray-100">{job.role || job.title}</p>
              <p className="text-sm text-gray-400 flex items-center gap-1.5">
                <Building2 size={13} /> {job.company}
              </p>
            </div>
            <button
              onClick={() => onSave(job)}
              disabled={saving}
              title={job.saved ? "Saved" : "Save"}
              className={`p-2 rounded-lg transition ${job.saved ? "text-cyan-400" : "text-gray-500 hover:text-gray-300"}`}
            >
              {job.saved ? <BookmarkCheck size={18} /> : <Bookmark size={18} />}
            </button>
          </div>

          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
            {job.type && <Badge tone="cyan">{job.type}</Badge>}
            {(job.location || job.remote) && (
              <span className="flex items-center gap-1"><MapPin size={12} /> {job.remote ? "Remote" : job.location}</span>
            )}
            {(job.stipend || job.ctc || job.salary_band) && (
              <span>{job.stipend || job.ctc || job.salary_band}</span>
            )}
            {job.deadline && (
              <span className="flex items-center gap-1"><Clock size={12} /> {job.deadline}</span>
            )}
          </div>

          {(job.required_skills || []).length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {(job.required_skills || []).slice(0, 8).map((s, i) => (
                <span key={i} className="text-[11px] px-2 py-0.5 rounded-full bg-gray-800 text-gray-400">{s}</span>
              ))}
            </div>
          )}

          {/* Trust + verification */}
          <p className="mt-2 text-[11px] text-gray-600">
            {job.posted_by_college ? `Posted by ${job.posted_by_college} Placement Cell` : "Verified by ATLAS AI"}
            {job.posted_date && ` · ${job.posted_date}`}
          </p>

          {/* Close the gap */}
          {lowMatch && gaps.length > 0 && (
            <div className="mt-3 rounded-xl border border-amber-900/50 bg-amber-950/20 p-3">
              <p className="text-xs text-amber-300 mb-1.5">Close the gap to raise your match:</p>
              <div className="flex flex-wrap gap-1.5">
                {gaps.slice(0, 4).map((g, i) => (
                  <button
                    key={i}
                    onClick={() => g.topic_id && navigate(`/learn/${g.topic_id}`)}
                    className="text-[11px] px-2 py-0.5 rounded-full bg-gray-800 text-amber-200 hover:bg-gray-700"
                  >
                    {g.name || g.label || g}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="mt-3 flex flex-wrap gap-2">
            <Button size="sm" variant="ghost" onClick={() => navigate("/resume")}>
              <FileText size={13} className="inline mr-1" /> Tailor resume
            </Button>
            {job.company && (
              <Button size="sm" variant="outline" onClick={() => navigate("/company")}>
                Prep for {job.company}
              </Button>
            )}
            {job.apply_link && (
              <a href={job.apply_link} target="_blank" rel="noreferrer"
                className="rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white px-3 py-1.5 text-xs font-medium">
                Apply
              </a>
            )}
          </div>

          {/* Tracker pipeline (only when saved) */}
          {job.saved && (
            <div className="mt-3 flex flex-wrap gap-1">
              {STAGES.map((stage) => (
                <button
                  key={stage}
                  onClick={() => onStatus(job, stage)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] capitalize transition ${
                    job.stage === stage
                      ? "bg-cyan-600 text-white"
                      : "bg-gray-800 text-gray-400 hover:text-gray-200"
                  }`}
                >
                  {stage}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}