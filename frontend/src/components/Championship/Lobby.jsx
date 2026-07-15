// Lobby.jsx - [NEW] pre-exam lobby
// FILE: frontend/src/components/Championship/Lobby.jsx
// BATCH 30 / v10 Championship (new) - The pre-exam lobby: upcoming / live /
// past championships, plus the rules gate. The rules are stated plainly
// (fullscreen, one attempt, hard timer, no re-entry) BEFORE entry so the
// lock later never feels like a trick — trust is a feature here.

import React, { useState } from "react";
import { Trophy, Clock, AlertTriangle, Users } from "lucide-react";
import { Badge, Button } from "../Common";

function statusTone(status) {
  if (status === "live") return "green";
  if (status === "scheduled") return "cyan";
  if (status === "published" || status === "closed") return "gray";
  return "gray";
}

export default function Lobby({ championships, onEnter, entering }) {
  const [confirming, setConfirming] = useState(null);

  const live = championships.filter((c) => c.status === "live");
  const upcoming = championships.filter((c) => c.status === "scheduled");
  const past = championships.filter(
    (c) => c.status === "published" || c.status === "closed"
  );

  const Card = ({ c }) => {
    const isLive = c.status === "live";
    const alreadyDone = c.attempted || c.my_attempt;
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-semibold text-gray-100">{c.title}</p>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-500">
              <Badge tone={statusTone(c.status)}>{c.status}</Badge>
              {c.college_name && (
                <span className="flex items-center gap-1"><Users size={12} /> {c.college_name}</span>
              )}
              {c.starts_at && (
                <span className="flex items-center gap-1"><Clock size={12} /> {c.starts_at}</span>
              )}
              <span>20 questions · 15 min</span>
            </div>
          </div>
          {isLive && !alreadyDone && (
            <Button size="sm" onClick={() => setConfirming(c)}>
              Enter
            </Button>
          )}
          {alreadyDone && <Badge tone="gray">Attempted</Badge>}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {live.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-emerald-400 flex items-center gap-2">
            <Trophy size={15} /> Live now
          </h2>
          {live.map((c) => <Card key={c.id} c={c} />)}
        </section>
      )}

      {upcoming.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-300">Upcoming</h2>
          {upcoming.map((c) => <Card key={c.id} c={c} />)}
        </section>
      )}

      {past.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-300">Past</h2>
          {past.map((c) => <Card key={c.id} c={c} />)}
        </section>
      )}

      {championships.length === 0 && (
        <p className="text-sm text-gray-500">
          No championships scheduled yet. Your college or ATLAS AI will announce
          the next one here.
        </p>
      )}

      {/* Rules gate */}
      {confirming && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setConfirming(null)}
        >
          <div
            className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 text-amber-400 mb-3">
              <AlertTriangle size={18} />
              <h3 className="text-lg font-semibold">Before you enter</h3>
            </div>
            <ul className="space-y-2 text-sm text-gray-300 mb-5">
              <li>• The exam runs <b>full-screen</b>. The clock is <b>15 minutes</b> and starts the moment you enter — it never pauses.</li>
              <li>• Leaving full-screen or switching tabs triggers <b>one warning</b> in the first 10 seconds. After that, it <b>locks and submits</b> your paper as-is.</li>
              <li>• You get <b>one attempt</b>. There is no re-entry.</li>
              <li>• The assistant is disabled during the exam.</li>
            </ul>
            <div className="flex gap-2">
              <Button
                full
                onClick={() => { const c = confirming; setConfirming(null); onEnter(c); }}
                disabled={entering}
              >
                {entering ? "Entering…" : "I understand — enter full-screen"}
              </Button>
              <Button variant="outline" onClick={() => setConfirming(null)}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}