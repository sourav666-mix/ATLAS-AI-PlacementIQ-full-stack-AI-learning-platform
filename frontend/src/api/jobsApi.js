// jobsApi.js - [NEW] board list (with match) + save + status
// FILE: frontend/src/api/jobsApi.js
// BATCH 29 / v10 Jobs Board (new) - board list (with personal match scores) +
// save + status tracking. Students never post — no create endpoint here.

import api from "./axios";

const jobsApi = {
  list: (params = {}) =>
    api.get("/jobs", { params }).then((r) => r.data),

  save: (jobId) =>
    api.post(`/jobs/${jobId}/save`).then((r) => r.data),

  setStatus: (jobId, stage) =>
    api.post(`/jobs/${jobId}/status`, { stage }).then((r) => r.data),
};

export default jobsApi;