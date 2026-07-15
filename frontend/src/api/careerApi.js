/**
 * ATLAS AI v12 — Career Target & Gap Engine API client.
 * Uses the shared axios instance (JWT interceptor + 401 redirect already applied).
 */
import api from "./axios";

const careerApi = {
  // ---- Type A (zero AI) -------------------------------------------------
  listCompanies: (domain) =>
    api.get("/career/companies", { params: { domain } }).then((r) => r.data),

  saveProfile: (payload) =>
    api.post("/career/profile", payload).then((r) => r.data),

  getProfile: () => api.get("/career/profile").then((r) => r.data),

  parseResume: (file) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/career/resume-parse", form).then((r) => r.data);
  },

  // read the cached report only — never triggers an AI call
  getReport: () => api.get("/career/report").then((r) => r.data),

  // ---- Type B (exactly one bounded AI call, cached by fingerprint) ------
  analyze: (force = false) =>
    api.post("/career/analyze", null, { params: { force } }).then((r) => r.data),
};

export default careerApi;