// frontend/src/store/liveLabV2Store.js   [NEW v12]
// The IDE shell's UI state: virtual file tree, editor tabs, script/notebook mode,
// notebook cells, and the terminal buffer. Composes alongside the v11 labStore
// (which still owns lab metadata + run state). All state is text-only -> zero storage cost.
import { create } from "zustand";
import { languageForPath } from "../utils/labKernel";

let _cellSeq = 1;
const newCellId = () => `cell_${_cellSeq++}_${Date.now().toString(36)}`;

export const useLiveLabStore = create((set, get) => ({
  // ---- files (text files are the source of truth here; binaries live in the FS) ----
  files: {
    "main.py": { content: "# Welcome to ATLAS Live Lab 2.0\nimport pandas as pd\nprint('ready')\n", language: "python", dirty: false, isBinary: false },
  },
  openTabs: ["main.py"],
  activeTab: "main.py",

  // ---- mode + notebook ----
  mode: "script", // 'script' | 'notebook'
  cells: [{ id: newCellId(), type: "code", source: "print('hello from a cell')", output: null, execCount: null, running: false }],

  // ---- terminal ----
  terminal: [{ stream: "system", text: "ATLAS kernel booting…" }],
  kernelStatus: "booting", // 'booting' | 'ready' | 'running'

  // ---------- file actions ----------
  setFileContent: (path, content) =>
    set((s) => ({ files: { ...s.files, [path]: { ...s.files[path], content, dirty: true } } })),

  markClean: (path) =>
    set((s) => (s.files[path] ? { files: { ...s.files, [path]: { ...s.files[path], dirty: false } } } : {})),

  createFile: (path, content = "", isBinary = false) =>
    set((s) => {
      if (s.files[path]) return {};
      const files = { ...s.files, [path]: { content, language: languageForPath(path), dirty: !isBinary, isBinary } };
      const openTabs = isBinary ? s.openTabs : Array.from(new Set([...s.openTabs, path]));
      return { files, openTabs, activeTab: isBinary ? s.activeTab : path };
    }),

  registerUploaded: (path) =>
    set((s) => ({ files: { ...s.files, [path]: { content: null, language: languageForPath(path), dirty: false, isBinary: true } } })),

  deleteFile: (path) =>
    set((s) => {
      const files = { ...s.files };
      delete files[path];
      const openTabs = s.openTabs.filter((p) => p !== path);
      const activeTab = s.activeTab === path ? openTabs[openTabs.length - 1] || null : s.activeTab;
      return { files, openTabs, activeTab };
    }),

  renameFile: (from, to) =>
    set((s) => {
      if (!s.files[from] || s.files[to]) return {};
      const files = { ...s.files, [to]: { ...s.files[from], language: languageForPath(to) } };
      delete files[from];
      const openTabs = s.openTabs.map((p) => (p === from ? to : p));
      const activeTab = s.activeTab === from ? to : s.activeTab;
      return { files, openTabs, activeTab };
    }),

  mergeFsPaths: (paths) =>
    set((s) => {
      const files = { ...s.files };
      for (const p of paths) if (!files[p]) files[p] = { content: null, language: languageForPath(p), dirty: false, isBinary: true };
      return { files };
    }),

  // ---------- tab actions ----------
  openTab: (path) => set((s) => ({ openTabs: Array.from(new Set([...s.openTabs, path])), activeTab: path })),
  closeTab: (path) =>
    set((s) => {
      const openTabs = s.openTabs.filter((p) => p !== path);
      const activeTab = s.activeTab === path ? openTabs[openTabs.length - 1] || null : s.activeTab;
      return { openTabs, activeTab };
    }),
  setActiveTab: (path) => set({ activeTab: path }),

  // ---------- mode ----------
  setMode: (mode) => set({ mode }),

  // ---------- notebook cells ----------
  addCell: (type = "code", afterId = null) =>
    set((s) => {
      const cell = { id: newCellId(), type, source: type === "markdown" ? "### Notes" : "", output: null, execCount: null, running: false };
      if (!afterId) return { cells: [...s.cells, cell] };
      const i = s.cells.findIndex((c) => c.id === afterId);
      const cells = [...s.cells];
      cells.splice(i + 1, 0, cell);
      return { cells };
    }),
  updateCell: (id, patch) => set((s) => ({ cells: s.cells.map((c) => (c.id === id ? { ...c, ...patch } : c)) })),
  removeCell: (id) => set((s) => ({ cells: s.cells.filter((c) => c.id !== id) })),
  moveCell: (id, dir) =>
    set((s) => {
      const i = s.cells.findIndex((c) => c.id === id);
      const j = dir === "up" ? i - 1 : i + 1;
      if (i < 0 || j < 0 || j >= s.cells.length) return {};
      const cells = [...s.cells];
      [cells[i], cells[j]] = [cells[j], cells[i]];
      return { cells };
    }),

  // ---------- terminal ----------
  appendTerminal: (stream, text) => set((s) => ({ terminal: [...s.terminal, { stream, text }].slice(-500) })),
  clearTerminal: () => set({ terminal: [] }),
  setKernelStatus: (kernelStatus) => set({ kernelStatus }),

  // ---------- persistence ----------
  serialize: () => {
    const s = get();
    const fileTree = Object.fromEntries(
      Object.entries(s.files).filter(([, f]) => !f.isBinary).map(([p, f]) => [p, f.content])
    );
    return {
      file_tree_json: { files: fileTree, mode: s.mode },
      notebook_cells_json: { cells: s.cells.map(({ id, type, source, execCount }) => ({ id, type, source, execCount })) },
    };
  },
  hydrate: ({ file_tree_json, notebook_cells_json } = {}) =>
    set((s) => {
      const next = {};
      if (file_tree_json?.files) {
        next.files = Object.fromEntries(
          Object.entries(file_tree_json.files).map(([p, content]) => [p, { content, language: languageForPath(p), dirty: false, isBinary: false }])
        );
        next.openTabs = Object.keys(next.files).slice(0, 3);
        next.activeTab = next.openTabs[0] || null;
      }
      if (file_tree_json?.mode) next.mode = file_tree_json.mode;
      if (notebook_cells_json?.cells?.length)
        next.cells = notebook_cells_json.cells.map((c) => ({ ...c, output: null, running: false }));
      return next;
    }),
}));