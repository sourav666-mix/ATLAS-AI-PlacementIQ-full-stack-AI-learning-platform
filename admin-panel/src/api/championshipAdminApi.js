// championshipAdminApi.js - [NEW] build / schedule / monitor / analyze / podium
// FILE: admin-panel/src/api/championshipAdminApi.js — BATCH 32 (new)
import api from "./axios";
const championshipAdminApi = {
  list: () => api.get("/admin/championships").then(r => r.data),
  create: (draft) => api.post("/admin/championships", draft).then(r => r.data),
  aiDraftPaper: (id, spec) => api.post(`/admin/championships/${id}/ai-draft`, spec).then(r => r.data),
  savePaper: (id, questions) => api.put(`/admin/championships/${id}/paper`, { questions }).then(r => r.data),
  schedule: (id, startsAt) => api.post(`/admin/championships/${id}/schedule`, { starts_at: startsAt }).then(r => r.data),
  monitor: (id) => api.get(`/admin/championships/${id}/monitor`).then(r => r.data),
  analyze: (id) => api.post(`/admin/championships/${id}/analyze`).then(r => r.data), // ONE AI call per event
  results: (id) => api.get(`/admin/championships/${id}/results`).then(r => r.data),
  podium: (id, podium) => api.post(`/admin/championships/${id}/podium`, { podium }).then(r => r.data),
  publish: (id) => api.post(`/admin/championships/${id}/publish`).then(r => r.data),
};
export default championshipAdminApi;