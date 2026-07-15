// frontend/src/components/LabPro/WorkspaceExplorer.jsx
/**
 * ATLAS AI 4.0 - v12 Live Lab Pro: workspace mode (the VS Code side).
 *
 * A real project tree (folders + multiple .py/.sql files) with multi-file
 * tabs. "Run file" first syncs every workspace .py into the shared
 * kernel's virtual FS, so `main.py` can `from src.utils import add` -
 * real project structure, not toy single files. Edits autosave through
 * the store's debounce (text only).
 */

import { useCallback, useState } from "react";
import useLabProStore from "../../store/labProStore";
import kernel from "./labProKernel";
import CellEditor from "./CellEditor";

export default function WorkspaceExplorer() {
  const {
    session, files, openTabs, activeTab, fileContents, error,
    openFile, closeTab, updateFileContent,
    createPath, renamePath, deletePath, setKernelStatus,
  } = useLabProStore();
  const [output, setOutput] = useState(null);
  const [running, setRunning] = useState(false);

  const runActiveFile = useCallback(async () => {
    if (!session || !activeTab) return;
    setRunning(true);
    const off = kernel.onStatus(setKernelStatus);
    try {
      // sync the whole tree so cross-file imports resolve
      await kernel.syncWorkspace(
        files.map((f) => ({ ...f, content: fileContents[f.path] }))
          .filter((f) => f.is_folder || f.path in fileContents || f.path === activeTab)
      );
      const source = fileContents[activeTab] ?? "";
      const out = await kernel.run(
        activeTab.endsWith(".sql") ? "sql" : "python",
        source
      );
      setOutput(out);
    } catch (err) {
      setOutput({ ok: false, text: `Kernel error: ${err.message}`, image: null });
    } finally {
      off();
      setRunning(false);
    }
  }, [session, activeTab, files, fileContents, setKernelStatus]);

  const promptNew = useCallback((isFolder) => {
    const path = window.prompt(
      isFolder ? "New folder path (e.g. src)" : "New file path (e.g. src/utils.py)"
    );
    if (path) createPath(path.trim(), isFolder);
  }, [createPath]);

  const promptRename = useCallback((oldPath) => {
    const next = window.prompt("Rename to:", oldPath);
    if (next && next !== oldPath) renamePath(oldPath, next.trim());
  }, [renamePath]);

  if (!session) return null;

  return (
    <div className="flex h-full min-h-[420px] rounded-lg border border-zinc-800 bg-zinc-900/60">
      {/* explorer sidebar */}
      <aside className="w-52 shrink-0 border-r border-zinc-800">
        <div className="flex items-center justify-between px-3 py-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
            Explorer
          </span>
          <span className="flex gap-2 text-zinc-500">
            <button type="button" title="New file" onClick={() => promptNew(false)}
              className="hover:text-sky-400">＋</button>
            <button type="button" title="New folder" onClick={() => promptNew(true)}
              className="hover:text-sky-400">📁</button>
          </span>
        </div>
        <ul className="overflow-auto px-1 text-sm">
          {files.map((f) => (
            <li key={f.path}
                className={`group flex items-center justify-between rounded px-2 py-1
                            ${activeTab === f.path ? "bg-zinc-800 text-sky-300" : "text-zinc-300 hover:bg-zinc-800/60"}`}
                style={{ paddingLeft: 8 + (f.path.split("/").length - 1) * 12 }}>
              <button
                type="button"
                className="min-w-0 flex-1 truncate text-left"
                onClick={() => !f.is_folder && openFile(f.path)}
              >
                {f.is_folder ? "▸ " : "· "}{f.path.split("/").pop()}
              </button>
              <span className="hidden gap-1 text-xs group-hover:flex">
                <button type="button" title="Rename" onClick={() => promptRename(f.path)}
                  className="text-zinc-500 hover:text-zinc-200">✎</button>
                <button type="button" title="Delete" onClick={() => deletePath(f.path)}
                  className="text-zinc-500 hover:text-red-400">✕</button>
              </span>
            </li>
          ))}
          {files.length === 0 && (
            <li className="px-2 py-2 text-xs text-zinc-600">
              Empty workspace - create main.py to start.
            </li>
          )}
        </ul>
      </aside>

      {/* editor + tabs + console */}
      <section className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center border-b border-zinc-800">
          <div className="flex min-w-0 flex-1 overflow-x-auto">
            {openTabs.map((p) => (
              <span key={p}
                    className={`flex items-center gap-2 border-r border-zinc-800 px-3 py-2 text-xs
                                ${activeTab === p ? "bg-zinc-800 text-sky-300" : "text-zinc-400"}`}>
                <button type="button" onClick={() => openFile(p)} className="truncate max-w-[140px]">
                  {p}
                </button>
                <button type="button" onClick={() => closeTab(p)}
                  className="text-zinc-600 hover:text-red-400">✕</button>
              </span>
            ))}
          </div>
          <button
            type="button"
            disabled={!activeTab || running}
            onClick={runActiveFile}
            className="m-1 rounded bg-emerald-600 px-3 py-1 text-xs font-semibold
                       text-white hover:bg-emerald-500 disabled:bg-zinc-700"
          >
            {running ? "Running…" : "▶ Run file"}
          </button>
        </div>

        <div className="flex-1 overflow-auto p-2">
          {activeTab ? (
            <CellEditor
              value={fileContents[activeTab] ?? ""}
              language={activeTab.endsWith(".sql") ? "sql" : "python"}
              minRows={14}
              onChange={(v) => updateFileContent(activeTab, v)}
              onRun={runActiveFile}
            />
          ) : (
            <div className="p-6 text-sm text-zinc-600">
              Open a file from the explorer, or create one.
            </div>
          )}
        </div>

        {(output || error) && (
          <div className={`max-h-48 overflow-auto border-t px-3 py-2 font-mono text-xs
                           whitespace-pre-wrap
                           ${output?.ok === false || error
                             ? "border-red-800 bg-red-950/40 text-red-300"
                             : "border-zinc-800 bg-zinc-950 text-zinc-300"}`}>
            {error || output?.text}
            {output?.image && (
              <img src={output.image} alt="run output chart"
                   className="mt-2 max-w-full rounded bg-white" />
            )}
          </div>
        )}
      </section>
    </div>
  );
}