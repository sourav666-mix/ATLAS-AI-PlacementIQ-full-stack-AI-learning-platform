// frontend/src/pages/LiveLabPro.jsx
/**
 * ATLAS AI 4.0 - v12 Live Lab Pro: the page.
 *
 * Layout (one kernel, three panels):
 *   header  - session title, env badge, kernel status, save state,
 *             Notebook <-> Workspace mode toggle
 *   left    - Files panel (Colab-style, local-only uploads)
 *   center  - NotebookView OR WorkspaceExplorer (per mode)
 *   right   - AI Copilot
 *
 * With no open session it shows the launcher: resume a session or start
 * a fresh Python / SQL scratch notebook (template cloned server-side,
 * zero AI calls). Routed at /labpro and /labpro/:sessionId - the roadmap
 * links here so the lab is one click from every topic (spec step 3).
 */

import { useEffect } from "react";
import { useParams } from "react-router-dom";
import useLabProStore from "../store/labProStore";
import kernel from "../components/LabPro/labProKernel";
import NotebookView from "../components/LabPro/NotebookView";
import WorkspaceExplorer from "../components/LabPro/WorkspaceExplorer";
import FilesPanel from "../components/LabPro/FilesPanel";
import LabProCopilot from "../components/LabPro/LabProCopilot";

const STATUS_LABEL = {
  cold: "kernel: idle",
  loading: "kernel: loading…",
  ready: "kernel: ready",
  error: "kernel: failed - reload the page",
};

const SAVE_LABEL = {
  saved: "saved",
  dirty: "unsaved changes…",
  saving: "saving…",
  error: "save failed - retrying on next edit",
};

function Launcher() {
  const { sessions, loadSessions, createSession, openSession, loading, error } =
    useLabProStore();

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <header>
        <h1 className="text-2xl font-bold text-zinc-100">Live Lab Pro</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Colab-style notebook + VS Code-style workspace, running on
          <span className="text-zinc-200"> your device</span>. Your files
          never leave this browser tab.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <button type="button" onClick={() => createSession("python")}
          className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-left hover:border-sky-600">
          <div className="text-lg font-semibold text-zinc-100">🐍 Python notebook</div>
          <div className="mt-1 text-xs text-zinc-500">
            pandas · NumPy · matplotlib · scikit-learn - upload a CSV and explore
          </div>
        </button>
        <button type="button" onClick={() => createSession("sql")}
          className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-left hover:border-sky-600">
          <div className="text-lg font-semibold text-zinc-100">🗄️ SQL notebook</div>
          <div className="mt-1 text-xs text-zinc-500">
            the MySQL practice subset: DDL, DML, joins, grouping, window functions
          </div>
        </button>
      </div>

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-400">
          Resume
        </h2>
        {loading && <p className="text-xs text-zinc-500">Loading…</p>}
        {error && <p className="text-xs text-red-400">{error}</p>}
        <ul className="divide-y divide-zinc-800 rounded-lg border border-zinc-800">
          {sessions.map((s) => (
            <li key={s.session_id}>
              <button type="button" onClick={() => openSession(s.session_id)}
                className="flex w-full items-center justify-between px-3 py-2 text-left hover:bg-zinc-900">
                <span className="truncate text-sm text-zinc-200">{s.title}</span>
                <span className="ml-3 shrink-0 text-xs text-zinc-500">
                  {s.active_env} · {s.cell_count} cells
                </span>
              </button>
            </li>
          ))}
          {!loading && sessions.length === 0 && (
            <li className="px-3 py-3 text-xs text-zinc-600">
              No sessions yet - start one above.
            </li>
          )}
        </ul>
      </section>
    </div>
  );
}

export default function LiveLabPro() {
  const { sessionId } = useParams();
  const { session, kernelStatus, saveState, setMode, openSession, closeSession } =
    useLabProStore();

  useEffect(() => {
    if (sessionId && sessionId !== session?.session_id) openSession(sessionId);
  }, [sessionId, session, openSession]);

  useEffect(() => {
    // pre-warm the kernel once a session is open (non-blocking)
    if (session) {
      const warm =
        session.active_env === "sql" ? kernel.ensureSql() : kernel.ensurePython();
      warm.catch(() => {});
    }
  }, [session]);

  if (!session) return <Launcher />;

  return (
    <div className="flex h-full min-h-screen flex-col bg-zinc-950">
      <header className="flex flex-wrap items-center gap-3 border-b border-zinc-800 px-4 py-2">
        <button type="button" onClick={closeSession}
          className="text-sm text-zinc-500 hover:text-zinc-200">←</button>
        <h1 className="truncate text-sm font-semibold text-zinc-100">
          {session.title}
        </h1>
        <span className="rounded bg-zinc-800 px-2 py-0.5 text-[11px] uppercase text-zinc-400">
          {session.active_env}
        </span>

        <div className="ml-auto flex items-center gap-3">
          <span className={`text-[11px] ${
            kernelStatus === "ready" ? "text-emerald-400"
            : kernelStatus === "error" ? "text-red-400" : "text-zinc-500"}`}>
            {STATUS_LABEL[kernelStatus] || kernelStatus}
          </span>
          <span className="text-[11px] text-zinc-500">{SAVE_LABEL[saveState]}</span>

          <div className="flex overflow-hidden rounded-md border border-zinc-700 text-xs">
            <button type="button" onClick={() => setMode("notebook")}
              className={`px-3 py-1 ${session.mode === "notebook"
                ? "bg-sky-700 text-white" : "text-zinc-400 hover:bg-zinc-800"}`}>
              Notebook
            </button>
            <button type="button" onClick={() => setMode("workspace")}
              className={`px-3 py-1 ${session.mode === "workspace"
                ? "bg-sky-700 text-white" : "text-zinc-400 hover:bg-zinc-800"}`}>
              Workspace
            </button>
          </div>
        </div>
      </header>

      <main className="grid flex-1 grid-cols-1 gap-3 p-3
                       lg:grid-cols-[220px_minmax(0,1fr)_300px]">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60">
          <FilesPanel />
        </div>

        <div className="min-w-0">
          {session.mode === "workspace" ? <WorkspaceExplorer /> : <NotebookView />}
        </div>

        <LabProCopilot />
      </main>
    </div>
  );
}