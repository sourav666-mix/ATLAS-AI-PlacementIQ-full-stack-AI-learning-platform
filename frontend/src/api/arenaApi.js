// arenaApi.js - [NEW] problem / run / submit / review
// FILE: frontend/src/api/arenaApi.js
// BATCH 27 / v10 Code Arena + DSA (new) - problem (bank-first serve) / run /
// submit+review, shared by Arena and DSA Gym. Defensive path resolution.

import api from "./axios";

async function firstOk(requests) {
  let lastErr = null;
  for (const run of requests) {
    try {
      return (await run()).data;
    } catch (err) {
      lastErr = err;
      const s = err?.response?.status;
      if (s && s !== 404 && s !== 405) throw err;
    }
  }
  throw lastErr;
}

const arenaApi = {
  // Serve a problem for a category x difficulty cell (bank-first; the backend
  // generates-once-and-caches on an empty cell). Backend route: GET /arena/next.
  problem: (params) =>
    firstOk([
      () => api.get("/arena/next", { params }),
    ]),

  // Run visible tests only — fast feedback, no points, no AI.
  // Backend route: POST /arena/run  body {problem_id, language, code}.
  run: (problem_id, language, code) =>
    firstOk([
      () => api.post("/arena/run", { problem_id, language, code }),
    ]),

  // Submit: runs hidden tests, then AI review, then progress_engine.
  // Backend route: POST /arena/problems/{id}/submit  body {language, code}.
  submit: (problem_id, language, code) =>
    firstOk([
      () =>
        api.post(`/arena/problems/${problem_id}/submit`, { language, code }),
    ]),

  // DSA topic explainers (Type A) + pattern-tagged topic list.
  dsaTopics: () =>
    firstOk([() => api.get("/dsa/topics"), () => api.get("/dsa")]),
  dsaTopic: (topicId) =>
    firstOk([
      () => api.get(`/dsa/topic/${topicId}`),
      () => api.get(`/dsa/topics/${topicId}`),
    ]),
};

export default arenaApi;