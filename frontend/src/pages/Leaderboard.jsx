// Leaderboard.jsx - [MOD] weekly podium + season + college
// FILE: frontend/src/pages/Leaderboard.jsx
// BATCH 30 / v10 Championship (new) - /leaderboard. Three scopes: weekly
// podium, season table (rolling 12 weeks), and college-vs-college (B2B).
// Read-only; ranks come from the server. REPLACES the Placeholder from B24.

import React, { useEffect, useState } from "react";
import { Trophy, Medal, Crown } from "lucide-react";
import championshipApi from "../api/championshipApi";
import useAuthStore from "../store/authStore";
import { Spinner } from "../components/Common";

const SCOPES = [
  { id: "weekly", label: "This week" },
  { id: "season", label: "Season" },
  { id: "college", label: "College vs College" },
];

const PODIUM_STYLE = [
  { icon: Crown, color: "#fbbf24", ring: "border-amber-500" },
  { icon: Medal, color: "#cbd5e1", ring: "border-gray-400" },
  { icon: Medal, color: "#f59e0b", ring: "border-amber-700" },
];

export default function Leaderboard() {
  const [scope, setScope] = useState("weekly");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const me = useAuthStore((s) => s.user);

  useEffect(() => {
    setLoading(true);
    setError(null);
    championshipApi
      .leaderboard(scope)
      .then((data) => {
        const list = Array.isArray(data) ? data : data.rows || data.leaderboard || [];
        setRows(list);
      })
      .catch((err) =>
        setError(String(err?.response?.data?.detail || "Couldn't load the leaderboard."))
      )
      .finally(() => setLoading(false));
  }, [scope]);

  const isCollege = scope === "college";
  const podium = rows.slice(0, 3);
  const rest = rows.slice(3);

  return (
    <div className="p-4 lg:p-6 max-w-3xl mx-auto space-y-5">
      <div className="rise" style={{ "--d": "0ms" }}>
        <h1 className="text-2xl font-bold text-gray-50">Leaderboard</h1>
        <p className="text-sm text-gray-500 mt-1">
          Where you stand across championships.
        </p>
      </div>

      <div className="rise flex gap-1 border-b border-gray-800" style={{ "--d": "60ms" }}>
        {SCOPES.map((s) => (
          <button
            key={s.id}
            onClick={() => setScope(s.id)}
            className={`px-4 py-2 text-sm border-b-2 -mb-px transition ${
              scope === s.id ? "border-cyan-500 text-cyan-300" : "border-transparent text-gray-500 hover:text-gray-300"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {loading ? (
        <div className="py-16 flex justify-center"><Spinner size={28} /></div>
      ) : rows.length === 0 ? (
        <p className="text-sm text-gray-500">
          No results yet for this view. Once a championship publishes, ranks
          appear here.
        </p>
      ) : (
        <>
          {/* Podium */}
          {!isCollege && podium.length >= 3 && (
            <div className="rise grid grid-cols-3 gap-3" style={{ "--d": "120ms" }}>
              {[podium[1], podium[0], podium[2]].map((row, displayIndex) => {
                const realRank = displayIndex === 1 ? 0 : displayIndex === 0 ? 1 : 2;
                const style = PODIUM_STYLE[realRank];
                const Icon = style.icon;
                const raise = displayIndex === 1 ? "sm:-translate-y-3" : "";
                return (
                  <div
                    key={row.user_id || row.id || displayIndex}
                    className={`bg-gray-900 border ${style.ring} rounded-2xl p-4 text-center ${raise}`}
                  >
                    <Icon size={22} className="mx-auto" style={{ color: style.color }} />
                    <p className="mt-2 text-sm font-semibold text-gray-100 truncate">
                      {row.name || row.full_name || "—"}
                    </p>
                    {row.college_name && (
                      <p className="text-[11px] text-gray-500 truncate">{row.college_name}</p>
                    )}
                    <p className="mt-1 text-lg font-bold tabular-nums" style={{ color: style.color }}>
                      {Math.round(row.score ?? row.points ?? 0)}
                    </p>
                  </div>
                );
              })}
            </div>
          )}

          {/* Table */}
          <div className="rise bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden" style={{ "--d": "180ms" }}>
            {(isCollege ? rows : rest).map((row, i) => {
              const rank = isCollege ? i + 1 : i + 4;
              const mine =
                me && (row.user_id === me.id || row.name === me.full_name);
              return (
                <div
                  key={row.user_id || row.id || i}
                  className={`flex items-center gap-3 px-4 py-3 border-b border-gray-800 last:border-0 ${
                    mine ? "bg-cyan-950/30" : ""
                  }`}
                >
                  <span className="text-sm text-gray-500 tabular-nums w-6">{rank}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-200 truncate">
                      {isCollege ? row.college_name : row.name || row.full_name}
                      {mine && <span className="ml-2 text-[11px] text-cyan-400">you</span>}
                    </p>
                    {!isCollege && row.college_name && (
                      <p className="text-[11px] text-gray-600 truncate">{row.college_name}</p>
                    )}
                  </div>
                  <span className="text-sm font-semibold text-gray-100 tabular-nums">
                    {Math.round(row.score ?? row.points ?? row.avg_score ?? 0)}
                  </span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}