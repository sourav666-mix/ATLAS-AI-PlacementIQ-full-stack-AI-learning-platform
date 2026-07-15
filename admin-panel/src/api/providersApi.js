// providersApi.js - AI provider health + kill-switch
// FILE: admin-panel/src/api/providersApi.js — BATCH 32 (new)
import api from "./axios";
const providersApi = {
  health: () => api.get("/admin/providers/health").then(r => r.data),
  toggle: (provider, enabled) => api.post(`/admin/providers/${provider}/toggle`, { enabled }).then(r => r.data),
};
export default providersApi;