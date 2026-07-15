// frontend/src/components/LabPro/NotebookView.jsx
/**
 * ATLAS AI 4.0 - v12 Live Lab Pro: notebook mode (the Colab side).
 *
 * Cells run per-cell (Shift+Enter or the play button) on the shared
 * kernel; outputs render inline under each cell - printed text, tables
 * (as monospace text) and matplotlib charts (runtime-only data-URLs that
 * are never persisted). Markdown cells toggle edit <-> preview.
 */

import { useCallback } from "react";
import useLabProStore from "../../store/labProStore";
import kernel from "./labProKernel";
import CellEditor from "./CellEditor";

function MarkdownPreview({ source }) {
  // minimal, dependency-free preview: headings, lists, paragraphs
  const lines = (source || "").split("\n");
  return (
    <div className="prose-sm text-zinc-200 space-y-1">
      {lines.map((ln, i) => {
        if (ln.startsWith("# "))
          return <h1 key={i} className="text-xl font-bold">{ln.slice(2)}</h1>;
        if (ln.startsWith("## "))
          return <h2 key={i} className="text-lg font-semibold">{ln.slice(3)}</h2>;
        if (ln.startsWith("- "))
          return <li key={i} className="ml-5 list-disc">{ln.slice(2)}</li>;
        return <p key={i}>{ln}</p>;
      })}
    </div>
  );
}

function CellOutput({ output }) {
  if (!output) return null;
  return (
    <div
      className={`mt-1 rounded-md border px-3 py-2 text-sm font-mono
                  whitespace-pre-wrap break-words
                  ${output.ok === false
                    ? "border-red-700 bg-red-950/40 text-red-300"
                    : "border-zinc-800 bg-zinc-950 text-zinc-300"}`}
    >
      {output.text}
      {output.image && (
        <img
          src={output.image}
          alt="cell chart output"
          className="mt-2 max-w-full rounded bg-white"
        />
      )}
    </div>
  );
}

export default function NotebookView() {
  const {
    session, cells, runtimeOutputs, runningCellId,
    updateCellSource, addCell, deleteCell, moveCell,
    setRuntimeOutput, setRunningCell, persistCellAfterRun, setKernelStatus,
  } = useLabProStore();

  const runCell = useCallback(
    async (cell) => {
      if (!session || cell.cell_type !== "code") return;
      setRunningCell(cell.id);
      const off = kernel.onStatus(setKernelStatus);
      try {
        const out = await kernel.run(session.active_env, cell.source);
        setRuntimeOutput(cell.id, out);
      } catch (err) {
        setRuntimeOutput(cell.id, {
          ok: false,
          text: `Kernel error: ${err.message}`,
          image: null,
        });
      } finally {
        off();
        setRunningCell(null);
        persistCellAfterRun(cell.id); // text-only save, fire-and-forget
      }
    },
    [session, setRunningCell, setRuntimeOutput, persistCellAfterRun, setKernelStatus]
  );

  if (!session) return null;

  return (
    <div className="space-y-3">
      {cells.map((cell) => (
        <div key={cell.id} className="group rounded-lg border border-zinc-800 bg-zinc-900/60 p-2">
          <div className="flex items-start gap-2">
            <button
              type="button"
              title={cell.cell_type === "code" ? "Run (Shift+Enter)" : "Markdown cell"}
              disabled={cell.cell_type !== "code" || runningCellId === cell.id}
              onClick={() => runCell(cell)}
              className="mt-1 h-7 w-7 shrink-0 rounded-full text-xs font-bold
                         bg-sky-600 text-white disabled:bg-zinc-700
                         hover:bg-sky-500"
            >
              {runningCellId === cell.id ? "…" : cell.cell_type === "code" ? "▶" : "M"}
            </button>

            <div className="min-w-0 flex-1">
              {cell.cell_type === "markdown" && cell.source && (
                <details>
                  <summary className="cursor-pointer text-xs text-zinc-500 mb-1">
                    edit markdown
                  </summary>
                  <CellEditor
                    value={cell.source}
                    language="markdown"
                    minRows={2}
                    onChange={(v) => updateCellSource(cell.id, v)}
                  />
                </details>
              )}
              {cell.cell_type === "markdown" && (
                <MarkdownPreview source={cell.source} />
              )}
              {cell.cell_type === "code" && (
                <CellEditor
                  value={cell.source}
                  language={session.active_env === "sql" ? "sql" : "python"}
                  onChange={(v) => updateCellSource(cell.id, v)}
                  onRun={() => runCell(cell)}
                  placeholder={session.active_env === "sql"
                    ? "-- SQL, runs on your device"
                    : "# Python, runs on your device"}
                />
              )}
              {cell.cell_type === "code" && (
                <CellOutput output={runtimeOutputs[cell.id]} />
              )}
            </div>

            <div className="flex flex-col gap-1 opacity-0 group-hover:opacity-100">
              <button type="button" title="Move up" className="text-zinc-500 hover:text-zinc-200"
                onClick={() => moveCell(cell.id, -1)}>↑</button>
              <button type="button" title="Move down" className="text-zinc-500 hover:text-zinc-200"
                onClick={() => moveCell(cell.id, 1)}>↓</button>
              <button type="button" title="Delete cell" className="text-zinc-500 hover:text-red-400"
                onClick={() => deleteCell(cell.id)}>✕</button>
            </div>
          </div>

          <div className="mt-1 flex gap-2 opacity-0 group-hover:opacity-100">
            <button type="button" onClick={() => addCell(cell.id, "code")}
              className="text-xs text-zinc-500 hover:text-sky-400">+ code</button>
            <button type="button" onClick={() => addCell(cell.id, "markdown")}
              className="text-xs text-zinc-500 hover:text-sky-400">+ markdown</button>
          </div>
        </div>
      ))}

      {cells.length === 0 && (
        <button type="button" onClick={() => addCell(null, "code")}
          className="w-full rounded-lg border border-dashed border-zinc-700
                     p-6 text-zinc-500 hover:border-sky-600 hover:text-sky-400">
          + first cell
        </button>
      )}
    </div>
  );
}