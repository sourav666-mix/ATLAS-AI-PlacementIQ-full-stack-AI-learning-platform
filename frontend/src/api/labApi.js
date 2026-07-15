// FILE: frontend/src/api/labApi.js
// BATCH 21 / v11 Phase 13 (new) - API client for the Batch 20 /lab surface.
// Uses the shared axios instance (src/api/axios.js) so the JWT is attached
// from the single source of truth (localStorage "atlas_token") and 401s go
// through the same session-reset/redirect handling as every other client.

import api from "./axios";

const http = api;

const labApi = {
  list: (domainId) =>
    http
      .get("/lab", { params: domainId ? { domain_id: domainId } : {} })
      .then((r) => r.data),

  get: (labId) => http.get(`/lab/${labId}`).then((r) => r.data),

  // Hidden test code for the BROWSER runner (tests execute in Pyodide)
  tests: (labId) => http.get(`/lab/${labId}/tests`).then((r) => r.data.tests),

  // Record in-browser results. NO AI happens on this path.
  grade: (labId, tasksPassed, codeSnapshot, artifacts) =>
    http
      .post("/lab/grade", {
        lab_id: labId,
        tasks_passed: tasksPassed,
        code_snapshot: codeSnapshot,
        artifacts: artifacts || undefined,
      })
      .then((r) => r.data),

  copilot: (mode, payload) =>
    http.post(`/lab/copilot/${mode}`, payload).then((r) => r.data),

  colabLaunch: (labId, code) =>
    http
      .post("/lab/colab-launch", { lab_id: labId, code })
      .then((r) => r.data),

  complete: (labId) =>
    http.post("/lab/complete", { lab_id: labId }).then((r) => r.data),
};

export default labApi;
