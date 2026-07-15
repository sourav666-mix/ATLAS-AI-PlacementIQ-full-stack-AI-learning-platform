// jobsAdminApi.js - [NEW] post / edit / expire / analytics
// FILE: admin-panel/src/api/jobsAdminApi.js — BATCH 32 (new)
import api from "./axios";
const jobsAdminApi = {
  list: () => api.get("/admin/jobs").then(r => r.data),
  create: (post) => api.post("/admin/jobs", post).then(r => r.data),
  update: (id, patch) => api.put(`/admin/jobs/${id}`, patch).then(r => r.data),
  expire: (id) => api.post(`/admin/jobs/${id}/expire`).then(r => r.data),
  analytics: (id) => api.get(`/admin/jobs/${id ? id + "/" : ""}analytics`).then(r => r.data),
};
export default jobsAdminApi;