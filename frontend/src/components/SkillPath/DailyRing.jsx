// DailyRing.jsx - daily points ring
// FILE: frontend/src/components/SkillPath/DailyRing.jsx
// BATCH 25 / v10 Dashboard (new) - Today's points ring + streak flame +
// next milestone. Numbers over percentages: the student thinks in points.

import React from "react";
import { Flame } from "lucide-react";
import { ProgressRing } from "../Common";

export default function DailyRing({ points, goal, streakDays, nextMilestone }) {
  const remaining = Math.max(0, goal - points);
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 flex items-center gap-5">
      <ProgressRing
        value={points}
        max={goal}
        size={104}
        stroke={9}
        color={points >= goal ? "#34d399" : "#22d3ee"}
        label={
          <div>
            <p className="text-xl font-bold text-gray-50 tabular-nums leading-none">
              {Math.round(points)}
            </p>
            <p className="text-[10px] text-gray-500 mt-0.5">of {goal} pts</p>
          </div>
        }
      />
      <div className="space-y-2">
        <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500">
          Today
        </p>
        <p className="text-sm text-gray-300">
          {points >= goal
            ? "Daily goal cleared — everything else is bonus."
            : `${Math.ceil(remaining)} points to today's goal.`}
        </p>
        <div className="flex items-center gap-2 text-amber-400">
          <Flame size={16} className={streakDays > 0 ? "" : "opacity-40"} />
          <span className="text-sm font-semibold tabular-nums">
            {streakDays}-day streak
          </span>
          {nextMilestone > streakDays && (
            <span className="text-[11px] text-gray-500">
              · {nextMilestone - streakDays} to the {nextMilestone}-day badge
            </span>
          )}
        </div>
      </div>
    </div>
  );
}