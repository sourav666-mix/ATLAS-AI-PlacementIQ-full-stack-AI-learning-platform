// FILE: frontend/src/components/LiveLab/ConsoleOutput.jsx
// BATCH 21 / v11 Phase 13 (new) - Live console: streams stdout/stderr from
// the worker and renders captured matplotlib figures inline as images.
// Tailwind dark theme; auto-scrolls to the newest line.

import React, { useEffect, useRef } from "react";

export default function ConsoleOutput({ output, onClear }) {
  const endRef = useRef(null);

  useEffect(() => {
    if (endRef.current) endRef.current.scrollIntoView({ behavior: "smooth" });
  }, [output]);

  return (
    <div className="flex flex-col h-full bg-gray-950 rounded-xl border border-gray-800">
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-800">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          Console — runs locally, nothing uploaded
        </span>
        <button
          onClick={onClear}
          className="text-xs text-gray-500 hover:text-gray-300"
        >
          clear
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-3 font-mono text-sm space-y-1">
        {output.length === 0 && (
          <p className="text-gray-600 italic">
            Run your code to see output here…
          </p>
        )}
        {output.map((line, index) => {
          if (line.kind === "figure") {
            return (
              <img
                key={index}
                src={line.dataUrl}
                alt="matplotlib figure"
                className="rounded-lg border border-gray-700 my-2 max-w-full bg-white"
              />
            );
          }
          const color =
            line.kind === "stderr"
              ? "text-red-400"
              : line.kind === "system"
              ? "text-cyan-600"
              : "text-gray-200";
          return (
            <pre key={index} className={`whitespace-pre-wrap ${color}`}>
              {line.text}
            </pre>
          );
        })}
        <div ref={endRef} />
      </div>
    </div>
  );
}