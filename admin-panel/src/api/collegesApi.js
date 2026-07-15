// collegesApi.js - college CRUD + bulk invite + seats
// FILE: admin-panel/src/api/collegesApi.js — BATCH 32 (new)
import api from "./axios";
const collegesApi = {
  list: () => api.get("/admin/colleges").then(r => r.data),
  create: (college) => api.post("/admin/colleges", college).then(r => r.data),
  update: (id, patch) => api.put(`/admin/colleges/${id}`, patch).then(r => r.data),
  bulkInvite: (id, csvText) => api.post(`/admin/colleges/${id}/bulk-invite`, { csv: csvText }).then(r => r.data),
  seats: (id) => api.get(`/admin/colleges/${id}/seats`).then(r => r.data),
};
export default collegesApi;