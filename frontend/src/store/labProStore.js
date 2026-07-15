// frontend/src/store/labProStore.js
/**
 * ATLAS AI 4.0 - v12 Live Lab Pro: Zustand store.
 *
 * Owns: session list, the open session, cells, run outputs (runtime-only
 * images live HERE and are never persisted), the workspace tree + open
 * tabs, and the debounced autosave pipeline.
 *
 * Autosave contract: edits mark the notebook dirty; a 1.5s debounce
 * PUTs the whole notebook (text only - the backend strips anything
 * binary). Post-run cell saves use the cheaper PATCH endpoint.
 */

import { create } from "zustand";
import labProApi from "../api/labProApi";

const AUTOSAVE_MS = 1500;
let autosaveTimer = null;
let fileSaveTimer = null;

function newCellId() {
  return `c-${Date.now().toString(36)}-${Math.random()
    .toString(36)
    .slice(2, 7)}`;
}

export const useLabProStore = create((set, get) => ({
  // ------------------------------ state --------------------------------
  sessions: [],
  session: null, // {session_id, title, mode, active_env}
  cells: [], // [{id, cell_type, source, output_text}]
  runtimeOutputs: {}, // cellId -> {text, image, ok} (images NEVER persisted)
  runningCellId: null,
  kernelStatus: "cold",
  saveState: "saved", // saved | dirty | saving | error

  files: [], // workspace tree [{path, is_folder, size_chars}]
  openTabs: [], // [path]
  activeTab: null,
  fileContents: {}, // path -> source (loaded lazily)

  loading: false,
  error: null,

  // ---------------------------- sessions -------------------------------
  loadSessions: async () => {
    set({ loading: true, error: null });
    try {
      const { sessions } = await labProApi.listSessions();
      set({ sessions, loading: false });
    } catch (err) {
      set({ error: err?.response?.data?.detail || err.message, loading: false });
    }
  },

  createSession: async (env) => {
    set({ loading: true, error: null });
    try {
      const s = await labProApi.createSession(env);
      set({
        session: s,
        cells: s.cells,
        runtimeOutputs: {},
        files: [],
        openTabs: [],
        activeTab: null,
        fileContents: {},
        saveState: "saved",
        loading: false,
      });
      get().loadSessions();
      return s;
    } catch (err) {
      set({ error: err?.response?.data?.detail || err.message, loading: false });
      return null;
    }
  },

  openSession: async (sid) => {
    set({ loading: true, error: null });
    try {
      const s = await labProApi.getSession(sid);
      const tree = await labProApi.getTree(sid);
      set({
        session: s,
        cells: s.cells,
        files: tree.files,
        runtimeOutputs: {},
        openTabs: [],
        activeTab: null,
        fileContents: {},
        saveState: "saved",
        loading: false,
      });
    } catch (err) {
      set({ error: err?.response?.data?.detail || err.message, loading: false });
    }
  },

  closeSession: () => set({ session: null, cells: [], runtimeOutputs: {} }),

  setMode: async (mode) => {
    const { session } = get();
    if (!session) return;
    set({ session: { ...session, mode } }); // optimistic - one kernel anyway
    try {
      await labProApi.setMode(session.session_id, mode);
    } catch {
      /* surface-only toggle; safe to ignore */
    }
  },

  setKernelStatus: (kernelStatus) => set({ kernelStatus }),

  // ------------------------------ cells --------------------------------
  updateCellSource: (cellId, source) => {
    set((st) => ({
      cells: st.cells.map((c) => (c.id === cellId ? { ...c, source } : c)),
      saveState: "dirty",
    }));
    get()._scheduleAutosave();
  },

  addCell: (afterId = null, cellType = "code") => {
    const cell = { id: newCellId(), cell_type: cellType, source: "", output_text: null };
    set((st) => {
      const idx = afterId ? st.cells.findIndex((c) => c.id === afterId) : st.cells.length - 1;
      const cells = [...st.cells];
      cells.splice(idx + 1, 0, cell);
      return { cells, saveState: "dirty" };
    });
    get()._scheduleAutosave();
    return cell.id;
  },

  deleteCell: (cellId) => {
    set((st) => ({
      cells: st.cells.filter((c) => c.id !== cellId),
      saveState: "dirty",
    }));
    get()._scheduleAutosave();
  },

  moveCell: (cellId, dir) => {
    set((st) => {
      const i = st.cells.findIndex((c) => c.id === cellId);
      const j = i + dir;
      if (i < 0 || j < 0 || j >= st.cells.length) return {};
      const cells = [...st.cells];
      [cells[i], cells[j]] = [cells[j], cells[i]];
      return { cells, saveState: "dirty" };
    });
    get()._scheduleAutosave();
  },

  setRuntimeOutput: (cellId, output) =>
    set((st) => ({
      runtimeOutputs: { ...st.runtimeOutputs, [cellId]: output },
    })),

  setRunningCell: (cellId) => set({ runningCellId: cellId }),

  /** Post-run persist of ONE cell (source + truncated text output). */
  persistCellAfterRun: async (cellId) => {
    const { session, cells, runtimeOutputs } = get();
    if (!session) return;
    const cell = cells.find((c) => c.id === cellId);
    if (!cell) return;
    const out = runtimeOutputs[cellId];
    try {
      await labProApi.patchCell(session.session_id, {
        id: cell.id,
        cell_type: cell.cell_type,
        source: cell.source,
        output_text: out?.text ? out.text.slice(0, 4000) : null,
      });
    } catch {
      set({ saveState: "error" });
    }
  },

  _scheduleAutosave: () => {
    if (autosaveTimer) clearTimeout(autosaveTimer);
    autosaveTimer = setTimeout(() => get()._flushAutosave(), AUTOSAVE_MS);
  },

  _flushAutosave: async () => {
    const { session, cells, runtimeOutputs } = get();
    if (!session) return;
    set({ saveState: "saving" });
    try {
      await labProApi.autosaveCells(
        session.session_id,
        cells.map((c) => ({
          id: c.id,
          cell_type: c.cell_type,
          source: c.source,
          output_text:
            runtimeOutputs[c.id]?.text?.slice(0, 4000) ??
            c.output_text ??
            null,
        }))
      );
      set({ saveState: "saved" });
    } catch {
      set({ saveState: "error" });
    }
  },

  // ---------------------------- workspace ------------------------------
  refreshTree: async () => {
    const { session } = get();
    if (!session) return;
    const tree = await labProApi.getTree(session.session_id);
    set({ files: tree.files });
  },

  openFile: async (path) => {
    const { session, openTabs, fileContents } = get();
    if (!session) return;
    if (!(path in fileContents)) {
      const f = await labProApi.readFile(session.session_id, path);
      set((st) => ({
        fileContents: { ...st.fileContents, [path]: f.content },
      }));
    }
    set({
      openTabs: openTabs.includes(path) ? openTabs : [...openTabs, path],
      activeTab: path,
    });
  },

  closeTab: (path) =>
    set((st) => {
      const openTabs = st.openTabs.filter((p) => p !== path);
      return {
        openTabs,
        activeTab:
          st.activeTab === path ? openTabs[openTabs.length - 1] || null : st.activeTab,
      };
    }),

  updateFileContent: (path, content) => {
    set((st) => ({
      fileContents: { ...st.fileContents, [path]: content },
      saveState: "dirty",
    }));
    if (fileSaveTimer) clearTimeout(fileSaveTimer);
    fileSaveTimer = setTimeout(async () => {
      const { session } = get();
      if (!session) return;
      set({ saveState: "saving" });
      try {
        const tree = await labProApi.upsertFile(
          session.session_id,
          path,
          get().fileContents[path] ?? ""
        );
        set({ files: tree.files, saveState: "saved" });
      } catch {
        set({ saveState: "error" });
      }
    }, AUTOSAVE_MS);
  },

  createPath: async (path, isFolder) => {
    const { session } = get();
    if (!session) return;
    try {
      const tree = await labProApi.upsertFile(session.session_id, path, "", isFolder);
      set({ files: tree.files, error: null });
      if (!isFolder) get().openFile(path);
    } catch (err) {
      set({ error: err?.response?.data?.detail || err.message });
    }
  },

  renamePath: async (oldPath, newPath) => {
    const { session } = get();
    if (!session) return;
    try {
      const tree = await labProApi.renamePath(session.session_id, oldPath, newPath);
      set((st) => ({
        files: tree.files,
        openTabs: st.openTabs.map((p) => (p === oldPath ? newPath : p)),
        activeTab: st.activeTab === oldPath ? newPath : st.activeTab,
        error: null,
      }));
    } catch (err) {
      set({ error: err?.response?.data?.detail || err.message });
    }
  },

  deletePath: async (path) => {
    const { session } = get();
    if (!session) return;
    const tree = await labProApi.deletePath(session.session_id, path);
    set((st) => ({
      files: tree.files,
      openTabs: st.openTabs.filter((p) => p !== path && !p.startsWith(path + "/")),
      activeTab:
        st.activeTab === path || st.activeTab?.startsWith(path + "/")
          ? null
          : st.activeTab,
    }));
  },
}));

export default useLabProStore;