// FILE: frontend/src/components/LiveLab/LabWorkspace.jsx   [v12 — FIXED, no optional imports]
// Multi-pane IDE shell: Explorer | Editor/Notebook | Terminal.
// Depends ONLY on Batch 4 files. No v11 imports, so it cannot white-screen.
import React, { useCallback, useEffect, useMemo, useRef } from "react";
import { usePyodide } from "../../hooks/usePyodideV2";
import { useLiveLabStore } from "../../store/liveLabV2Store";
import { KERNEL_INIT, CAPTURE_CALL, parseOutput } from "../../utils/labKernel";
import FileExplorerPanel from "./FileExplorerPanel";
import EditorTabs from "./EditorTabs";
import NotebookCellRunner from "./NotebookCellRunner";
import IntegratedTerminal from "./IntegratedTerminal";
import CommandPalette from "./CommandPalette";

export default function LabWorkspace({ domainId }) {
  const kernel = usePyodide();
  const store = useLiveLabStore();
  const {
    mode, setMode, files, activeTab, cells,
    appendTerminal, clearTerminal, setKernelStatus, kernelStatus,
  } = store;
  const initedRef = useRef(false);

  // init kernel once ready (matplotlib Agg backend + figure flusher)
  useEffect(() => {
    if (kernel.ready && !initedRef.current) {
      initedRef.current = true;
      kernel
        .runCode(KERNEL_INIT)
        .then(() => {
          appendTerminal("system", "kernel ready — runs on your device, 0 GPU\n");
          setKernelStatus("ready");
        })
        .catch((e) => appendTerminal("stderr", `kernel init failed: ${e.message}\n`));
    }
  }, [kernel.ready]); // eslint-disable-line

  // write text files into the virtual FS so imports / read_csv work by path
  const syncBeforeRun = useCallback(async () => {
    for (const [path, f] of Object.entries(files)) {
      if (!f.isBinary && f.content != null) {
        await kernel.writeFile(path, new TextEncoder().encode(f.content));
      }
    }
  }, [files, kernel]);

  const runActive = useCallback(async () => {
    if (!activeTab) return;
    const code = files[activeTab]?.content ?? "";
    setKernelStatus("running");
    appendTerminal("system", `\n$ python ${activeTab}\n`);
    let buffer = "";
    try {
      await syncBeforeRun();
      await kernel.runCode(code, (stream, text) => {
        buffer += text;
        appendTerminal(stream, text);
      });
      await kernel.runCode(CAPTURE_CALL, (_s, text) => { buffer += text; });
      const { images } = parseOutput(buffer);
      if (images.length) appendTerminal("system", `[${images.length} chart(s) rendered]\n`);
    } catch (e) {
      appendTerminal("stderr", (e?.message || String(e)) + "\n");
    } finally {
      setKernelStatus("ready");
    }
  }, [activeTab, files, kernel, syncBeforeRun, appendTerminal, setKernelStatus]);

  const commands = useMemo(
    () => [
      { label: "Run active file", hint: "▶", run: runActive },
      {
        label: mode === "script" ? "Switch to Notebook Mode" : "Switch to Script Mode",
        run: () => setMode(mode === "script" ? "notebook" : "script"),
      },
      { label: "Clear terminal", run: clearTerminal },
      {
        label: "Restart kernel",
        run: () =>
          kernel.resetKernel().then(() => {
            initedRef.current = false;
            appendTerminal("system", "kernel restarted\n");
          }),
      },
    ],
    [runActive, mode, setMode, clearTerminal, kernel, appendTerminal]
  );

  return (
    <div className="h-[calc(100vh-14rem)] flex flex-col rounded-xl border border-gray-800 overflow-hidden bg-gray-950 text-gray-100">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-3 py-2 border-b border-gray-800">
        <button
          onClick={runActive}
          disabled={kernelStatus === "running" || !kernel.ready}
          className="rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-40 px-3 py-1.5 text-sm font-medium"
        >
          ▶ Run
        </button>
        <div className="flex rounded-lg bg-gray-900 p-0.5 border border-gray-800">
          {["script", "notebook"].map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 py-1 rounded-md text-sm ${
                mode === m ? "bg-violet-600 text-white" : "text-gray-400"
              }`}
            >
              {m === "script" ? "Script" : "Notebook"}
            </button>
          ))}
        </div>
        <span className="flex-1" />
        <span className="text-xs text-gray-500">Ctrl/⌘K for commands</span>
      </div>

      {/* Body */}
      <div className="flex-1 flex min-h-0">
        <div className="w-56 shrink-0">
          <FileExplorerPanel kernel={kernel} />
        </div>
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex-1 min-h-0">
            {mode === "script" ? (
              <EditorTabs />
            ) : (
              <NotebookCellRunner kernel={kernel} syncBeforeRun={syncBeforeRun} />
            )}
          </div>
          <div className="h-48 shrink-0">
            <IntegratedTerminal />
          </div>
        </div>
      </div>

      {/* Status bar */}
      <div className="flex items-center gap-4 px-3 py-1 border-t border-gray-800 bg-violet-600/10 text-[11px] text-gray-400">
        <span className={kernelStatus === "running" ? "text-amber-400" : "text-emerald-400"}>
          ● Kernel {kernelStatus}
        </span>
        <span>{mode === "script" ? `Script · ${activeTab || "—"}` : `Notebook · ${cells.length} cells`}</span>
        <span className="flex-1" />
        <span>0 GPU · runs on your device</span>
      </div>

      <CommandPalette commands={commands} />
    </div>
  );
}