// companyApi.js - intel report + compare + gap map
// FILE: frontend/src/api/companyApi.js
// BATCH 31 / v10 Company Intel (new) - cache-first report + gap map + compare.
// The gap map is pure server-side set math over the student's radar; no
// per-student AI. Reports are cached 30 days server-side.

import api from "./axios";

async function firstOk(requests) {
  let lastErr = null;
  for (const run of requests) {
    try { return (await run()).data; }
    catch (err) {
      lastErr = err;
      const s = err?.response?.status;
      if (s && s !== 404 && s !== 405) throw err;
    }
  }
  throw lastErr;
}

const companyApi = {
  list: () =>
    firstOk([() => api.get("/company"), () => api.get("/company/list")]),

  report: (slug) =>
    firstOk([
      () => api.get(`/company/${slug}`),
      () => api.get(`/company/report/${slug}`),
    ]),

  gapMap: (slug) =>
    firstOk([
      () => api.get(`/company/${slug}/gap-map`),
      () => api.get(`/company/${slug}/gap`),
    ]),

  compare: (slugA, slugB) =>
    api.get("/company/compare", { params: { a: slugA, b: slugB } }).then((r) => r.data),
};

export default companyApi;