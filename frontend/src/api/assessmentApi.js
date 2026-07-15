// assessmentApi.js - [MOD] mock interview + aptitude + analytics
// FILE: frontend/src/api/assessmentApi.js
// BATCH 31 / v10 Assessment Center (new) - merged Mock Interview (text) +
// Aptitude + lifetime analytics. Defensive path resolution.

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

const assessmentApi = {
  // Mock Interview (text) — start returns a question set; submit scores answers.
  startMock: ({ role, company, level }) =>
    firstOk([
      () => api.post("/assessment/mock/start", { role, company, level }),
      () => api.post("/assessment/interview/start", { role, company, level }),
    ]),
  submitMock: (sessionId, answers) =>
    firstOk([
      () => api.post(`/assessment/mock/${sessionId}/submit`, { answers }),
      () => api.post("/assessment/mock/submit", { session_id: sessionId, answers }),
    ]),

  // Aptitude — generate a set for a category/preset; submit for scoring.
  startAptitude: ({ category, preset }) =>
    firstOk([
      () => api.post("/assessment/aptitude/start", { category, preset }),
      () => api.post("/assessment/aptitude/generate", { category, preset }),
    ]),
  submitAptitude: (sessionId, answers) =>
    firstOk([
      () => api.post(`/assessment/aptitude/${sessionId}/submit`, { answers }),
      () => api.post("/assessment/aptitude/submit", { session_id: sessionId, answers }),
    ]),

  analytics: () =>
    firstOk([
      () => api.get("/assessment/analytics"),
      () => api.get("/assessment/my-analytics"),
    ]),
};

export default assessmentApi;