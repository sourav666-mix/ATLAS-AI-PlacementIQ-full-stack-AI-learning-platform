// InterviewerAvatar.jsx - [NEW] speaking-animation interviewer
// FILE: frontend/src/components/Studio/InterviewerAvatar.jsx
// BATCH 31 / v10 Interview Studio (new) - The AI interviewer presence: an
// abstract avatar with a speaking animation (animated rings while TTS plays).
// Purely visual; keeps the session feeling like a real video call.

import React from "react";
import { Bot } from "lucide-react";

export default function InterviewerAvatar({ speaking, thinking }) {
  return (
    <div className="relative rounded-2xl overflow-hidden bg-gradient-to-br from-gray-900 to-gray-950 border border-gray-800 aspect-video flex items-center justify-center">
      <div className="relative">
        {speaking && (
          <>
            <span className="absolute inset-0 -m-4 rounded-full bg-cyan-500/20 animate-ping" />
            <span className="absolute inset-0 -m-8 rounded-full bg-cyan-500/10 animate-pulse" />
          </>
        )}
        <div
          className="relative h-20 w-20 rounded-full flex items-center justify-center"
          style={{
            background:
              "radial-gradient(120% 120% at 30% 20%, #22d3ee 0%, #0e7490 60%, #0b3b47 100%)",
          }}
        >
          <Bot size={34} className="text-gray-950" />
        </div>
      </div>
      <div className="absolute bottom-3 left-0 right-0 text-center">
        <span className="text-xs text-gray-400">
          {thinking ? "Evaluating your answer…" : speaking ? "Interviewer is speaking" : "Interviewer"}
        </span>
      </div>
    </div>
  );
}