// LiveSubtitles.jsx - [NEW] question/answer subtitles
// FILE: frontend/src/components/Studio/LiveSubtitles.jsx
// BATCH 31 / v10 Interview Studio (new) - Subtitles for the current question
// plus the student's live transcript as they speak (Web Speech STT). Answers
// are TEXT only; that's what gets stored and scored.

import React from "react";

export default function LiveSubtitles({ question, transcript, interim, listening }) {
  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900 p-5 space-y-4">
      <div>
        <p className="text-[11px] uppercase tracking-[0.14em] text-cyan-400 mb-1">Question</p>
        <p className="text-base text-gray-100 leading-relaxed">{question || "…"}</p>
      </div>
      <div>
        <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500 mb-1">
          Your answer {listening && <span className="text-cyan-400 animate-pulse">· listening</span>}
        </p>
        <p className="text-sm text-gray-300 leading-relaxed min-h-[3rem]">
          {transcript}
          {interim && <span className="text-gray-500"> {interim}</span>}
          {!transcript && !interim && (
            <span className="text-gray-600">Speak your answer, or type it below.</span>
          )}
        </p>
      </div>
    </div>
  );
}