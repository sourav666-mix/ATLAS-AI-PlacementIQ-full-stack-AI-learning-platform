// frontend/src/components/LiveLab/IntegratedTerminal.jsx   [NEW v12]
// VS Code-style integrated terminal: persistent stdout/stderr scrollback with autoscroll + clear.
import { useEffect, useRef } from "react";
import { useLiveLabStore } from "../../store/liveLabV2Store";

const COLOR = { stdout: "text-zinc-200", stderr: "text-rose-400", system: "text-violet-400" };

export default function IntegratedTerminal() {
  const { terminal, clearTerminal, kernelStatus } = useLiveLabStore();
  const endRef = useRef(null);
  useEffect(() => { endRef.current?.scrollIntoView({ block: "end" }); }, [terminal]);

  return (
    <div className="h-full flex flex-col bg-black/60 border-t border-zinc-800">
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-zinc-800">
        <span className="text-xs font-semibold uppercase tracking-wide text-zinc-400">Terminal</span>
        <div className="flex items-center gap-3">
          <span className={`text-xs ${kernelStatus === "running" ? "text-amber-400" : "text-emerald-400"}`}>
            {kernelStatus === "running" ? "● running" : "● ready"}
          </span>
          <button onClick={clearTerminal} className="text-xs text-zinc-500 hover:text-zinc-200">clear</button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-3 py-2 font-mono text-[13px] leading-relaxed">
        {terminal.map((l, i) => (
          <span key={i} className={`${COLOR[l.stream] || "text-zinc-300"} whitespace-pre-wrap`}>{l.text}</span>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}