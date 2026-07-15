// RadarChart.jsx - skill radar (Recharts)
// FILE: frontend/src/components/Charts/RadarChart.jsx
// BATCH 25 / v10 Dashboard (new) - Skill radar (Recharts), tuned for the
// dark theme: soft grid, cyan fill, quiet axis labels. Data: [{skill, score}].

import React from "react";
import {
  Radar, RadarChart as ReRadarChart, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, ResponsiveContainer, Tooltip,
} from "recharts";

export default function RadarChart({ data = [], height = 260 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ReRadarChart data={data} outerRadius="72%">
        <PolarGrid stroke="#1f2937" />
        <PolarAngleAxis
          dataKey="skill"
          tick={{ fill: "#9ca3af", fontSize: 11 }}
        />
        <PolarRadiusAxis
          domain={[0, 100]}
          tick={false}
          axisLine={false}
        />
        <Tooltip
          contentStyle={{
            background: "#0b1220",
            border: "1px solid #1f2937",
            borderRadius: 12,
            fontSize: 12,
            color: "#e5e7eb",
          }}
          formatter={(value) => [`${Math.round(value)} / 100`, "mastery"]}
        />
        <Radar
          dataKey="score"
          stroke="#22d3ee"
          fill="#22d3ee"
          fillOpacity={0.22}
          strokeWidth={2}
          isAnimationActive
          animationDuration={700}
        />
      </ReRadarChart>
    </ResponsiveContainer>
  );
}