// studentsApi.js - student search / detail / override
// FILE: admin-panel/src/api/studentsApi.js — BATCH 32 (new)
import api from "./axios";
const studentsApi = {
  search: (q) => api.get("/admin/students", { params: { q } }).then(r => r.data),
  detail: (id) => api.get(`/admin/students/${id}`).then(r => r.data),
  resetAttempts: (id, championshipId) => api.post(`/admin/students/${id}/reset-attempt`, { championship_id: championshipId }).then(r => r.data),
  grantPlan: (id, plan) => api.post(`/admin/students/${id}/grant-plan`, { plan }).then(r => r.data),
  exportReport: (id) => api.get(`/admin/students/${id}/export`).then(r => r.data),
};
export default studentsApi;