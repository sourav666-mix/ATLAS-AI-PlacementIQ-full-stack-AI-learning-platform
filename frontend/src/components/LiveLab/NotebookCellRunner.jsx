// frontend/src/components/LiveLab/NotebookCellRunner.jsx   [NEW v12]
// Colab-style notebook: markdown + code cells, run cell-by-cell in the SAME kernel session
// (variables persist across cells), per-cell output with inline charts, reorder/add/delete.
import Editor from "@monaco-editor/react";
import { useLiveLabStore } from "../../store/liveLabV2Store";
import { CAPTURE_CALL, parseOutput } from "../../utils/labKernel";

function renderMarkdown(src = "") {
  return src.split("\n").map((line, i) => {
    if (line.startsWith("### ")) return <h3 key={i} className="text-base font-semibold text-zinc-100 mt-1">{line.slice(4)}</h3>;
    if (line.startsWith("## ")) return <h2 key={i} className="text-lg font-semibold text-zinc-100 mt-1">{line.slice(3)}</h2>;
    if (line.startsWith("# ")) return <h1 key={i} className="text-xl font-bold text-zinc-100 mt-1">{line.slice(2)}</h1>;
    if (line.startsWith("- ")) return <li key={i} className="text-zinc-300 ml-4 list-disc">{line.slice(2)}</li>;
    if (!line.trim()) return <div key={i} className="h-2" />;
    return <p key={i} className="text-zinc-300">{line}</p>;
  });
}

function Cell({ cell, kernel, syncBeforeRun }) {
  const { updateCell, removeCell, moveCell, addCell, appendTerminal, setKernelStatus } = useLiveLabStore();

  const run = async () => {
    if (cell.type === "markdown") return updateCell(cell.id, { output: { rendered: true } });
    updateCell(cell.id, { running: true, output: null });
    setKernelStatus("running");
    let buffer = "";
    try {
      await syncBeforeRun();
      await kernel.runCode(cell.source, (stream, text) => { buffer += text; appendTerminal(stream, text); });
      await kernel.runCode(CAPTURE_CALL, (_s, text) => { buffer += text; }); // flush figures
      const { text, images } = parseOutput(buffer);
      updateCell(cell.id, { running: false, output: { text, images, error: null }, execCount: (cell.execCount || 0) + 1 });
    } catch (e) {
      updateCell(cell.id, { running: false, output: { text: "", images: [], error: e.message } });
    } finally {
      setKernelStatus("ready");
    }
  };

  return (
    <div className="group rounded-xl border border-zinc-800 bg-zinc-900/50 overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-zinc-800 text-xs text-zinc-500">
        <button onClick={run} className="rounded bg-violet-600 hover:bg-violet-500 text-white px-2 py-0.5">▶ Run</button>
        <span>{cell.type === "code" ? `[${cell.execCount ?? " "}]` : "markdown"}</span>
        <span className="flex-1" />
        <button onClick={() => moveCell(cell.id, "up")} className="hover:text-zinc-200">↑</button>
        <button onClick={() => moveCell(cell.id, "down")} className="hover:text-zinc-200">↓</button>
        <button onClick={() => addCell("code", cell.id)} className="hover:text-zinc-200">＋code</button>
        <button onClick={() => addCell("markdown", cell.id)} className="hover:text-zinc-200">＋md</button>
        <button onClick={() => removeCell(cell.id)} className="hover:text-rose-400">✕</button>
      </div>

      {cell.type === "code" ? (
        <Editor
          height="120px"
          theme="vs-dark"
          language="python"
          value={cell.source}
          onChange={(v) => updateCell(cell.id, { source: v ?? "" })}
          options={{ minimap: { enabled: false }, fontSize: 13, scrollBeyondLastLine: false, lineNumbers: "off", automaticLayout: true }}
        />
      ) : cell.output?.rendered ? (
        <div className="p-3 space-y-1" onDoubleClick={() => updateCell(cell.id, { output: null })}>{renderMarkdown(cell.source)}</div>
      ) : (
        <textarea
          value={cell.source}
          onChange={(e) => updateCell(cell.id, { source: e.target.value })}
          className="w-full h-24 bg-transparent p-3 text-zinc-200 text-sm outline-none resize-none font-mono"
          placeholder="Markdown — double-click output to re-edit"
        />
      )}

      {cell.output && cell.type === "code" && (
        <div className="border-t border-zinc-800 p-3 space-y-2">
          {cell.output.error ? (
            <pre className="text-rose-400 text-sm whitespace-pre-wrap">{cell.output.error}</pre>
          ) : (
            <>
              {cell.output.text && <pre className="text-zinc-300 text-sm whitespace-pre-wrap overflow-x-auto">{cell.output.text}</pre>}
              {cell.output.images?.map((src, i) => <img key={i} src={src} alt="figure" className="max-w-full rounded border border-zinc-800" />)}
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default function NotebookCellRunner({ kernel, syncBeforeRun }) {
  const { cells, addCell } = useLiveLabStore();
  return (
    <div className="h-full overflow-y-auto p-4 space-y-3 bg-zinc-950">
      {cells.map((c) => <Cell key={c.id} cell={c} kernel={kernel} syncBeforeRun={syncBeforeRun} />)}
      <div className="flex gap-2">
        <button onClick={() => addCell("code")} className="rounded-lg border border-zinc-800 px-3 py-1.5 text-sm text-zinc-300 hover:border-violet-500/60">＋ Code cell</button>
        <button onClick={() => addCell("markdown")} className="rounded-lg border border-zinc-800 px-3 py-1.5 text-sm text-zinc-300 hover:border-violet-500/60">＋ Markdown cell</button>
      </div>
    </div>
  );
}