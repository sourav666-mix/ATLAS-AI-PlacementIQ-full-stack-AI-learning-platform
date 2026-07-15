// CameraTile.jsx - [NEW] getUserMedia mirror (nothing uploaded)
// FILE: frontend/src/components/Studio/CameraTile.jsx
// BATCH 31 / v10 Interview Studio (new) - The mirror preview tile. Mirrored
// like a video call. Shows a live presence readout and a persistent "not
// recorded" reassurance. The <video> is local-only; nothing is captured.

import React from "react";
import { VideoOff } from "lucide-react";

export default function CameraTile({ videoRef, active, presencePct, facePresent, error }) {
  return (
    <div className="relative rounded-2xl overflow-hidden bg-gray-950 border border-gray-800 aspect-video">
      <video
        ref={videoRef}
        muted
        playsInline
        className="w-full h-full object-cover"
        style={{ transform: "scaleX(-1)" }}
      />
      {!active && (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-600 gap-2">
          <VideoOff size={28} />
          <p className="text-xs px-4 text-center">{error || "Camera off"}</p>
        </div>
      )}
      {active && (
        <>
          <div className="absolute top-2 left-2 flex items-center gap-1.5 rounded-full bg-black/60 px-2.5 py-1">
            <span className={`h-2 w-2 rounded-full ${facePresent ? "bg-emerald-400" : "bg-amber-400"}`} />
            <span className="text-[11px] text-gray-200 tabular-nums">{presencePct}% present</span>
          </div>
          <div className="absolute bottom-2 left-2 right-2 text-center">
            <span className="text-[10px] text-gray-400 bg-black/50 rounded px-2 py-0.5">
              Not recorded · numbers only
            </span>
          </div>
        </>
      )}
    </div>
  );
}