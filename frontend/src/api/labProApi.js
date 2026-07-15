// frontend/src/api/labProApi.js
/**
 * ATLAS AI 4.0 - v12 Live Lab Pro: API client.
 *
 * Every function maps 1:1 to a backend endpoint from routers/lab_pro.py.
 * Uses the platform's shared axios instance (JWT interceptor lives there),
 * so this file adds ZERO auth logic of its own.
 */

import api from "./axios"; // the v10 student-app axios instance (JWT attached)

// ------------------------------- notebook -------------------------------

export const labProApi = {
  listTemplates: () =>
    api.get("/labpro/templates").then((r) => r.data),

  createSession: (env, title = null) =>
    api.post("/labpro/session", { env, title }).then((r) => r.data),

  listSessions: () =>
    api.get("/labpro/sessions").then((r) => r.data),

  getSession: (sid) =>
    api.get(`/labpro/session/${sid}`).then((r) => r.data),

  /** Whole-notebook autosave (debounced by the store). Text only. */
  autosaveCells: (sid, cells) =>
    api.put(`/labpro/session/${sid}/cells`, { cells }).then((r) => r.data),

  /** Single-cell save right after a run - cheaper than a full save. */
  patchCell: (sid, cell) =>
    api.patch(`/labpro/session/${sid}/cell`, { cell }).then((r) => r.data),

  setMode: (sid, mode) =>
    api.put(`/labpro/session/${sid}/mode`, { mode }).then((r) => r.data),

  // ------------------------------ workspace -----------------------------

  getTree: (sid) =>
    api.get(`/labpro/session/${sid}/files`).then((r) => r.data),

  readFile: (sid, path) =>
    api
      .get(`/labpro/session/${sid}/file`, { params: { path } })
      .then((r) => r.data),

  upsertFile: (sid, path, content = "", isFolder = false) =>
    api
      .put(`/labpro/session/${sid}/file`, {
        path,
        content,
        is_folder: isFolder,
      })
      .then((r) => r.data),

  renamePath: (sid, oldPath, newPath) =>
    api
      .post(`/labpro/session/${sid}/file/rename`, {
        old_path: oldPath,
        new_path: newPath,
      })
      .then((r) => r.data),

  deletePath: (sid, path) =>
    api
      .delete(`/labpro/session/${sid}/file`, { params: { path } })
      .then((r) => r.data),

  // ------------------------------- copilot ------------------------------

  /** Type B on cache miss (bounded by the daily cap); FREE on cache hit. */
  copilot: ({ action, code, errorText = null, goal = null, env = "python" }) =>
    api
      .post("/labpro/copilot", {
        action,
        code,
        error_text: errorText,
        goal,
        env,
      })
      .then((r) => r.data),
};

export default labProApi;