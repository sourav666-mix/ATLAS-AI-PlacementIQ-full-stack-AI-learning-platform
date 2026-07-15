// championshipApi.js - [NEW] enter / answer / submit / result + proctor events
// FILE: frontend/src/api/championshipApi.js
// BATCH 30 / v10 Championship (new) - list / enter / answer autosave / submit
// / result + the proctor violation event. The server owns the timer and the
// one-attempt constraint; the client just reports.

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

const championshipApi = {
  list: () =>
    firstOk([
      () => api.get("/championship"),
      () => api.get("/championship/list"),
      () => api.get("/championships"),
    ]),

  // Enter -> server records entry_timestamp, returns paper + server deadline.
  enter: (championshipId) =>
    api.post(`/championship/${championshipId}/enter`).then((r) => r.data),

  // Autosave a single answer (best-effort; the exam continues if it fails).
  answer: (championshipId, questionIndex, answer) =>
    api
      .put(`/championship/${championshipId}/answer`, {
        question_index: questionIndex,
        answer,
      })
      .then((r) => r.data),

  // Submit the whole sheet (also called by the guard on lock).
  submit: (championshipId, answers, meta = {}) =>
    api
      .post(`/championship/${championshipId}/submit`, { answers, ...meta })
      .then((r) => r.data),

  // Proctor violation -> server sets locked=1, increments fullscreen_exits.
  violation: (championshipId, kind = "fullscreen_exit") =>
    api
      .post(`/championship/${championshipId}/violation`, { kind })
      .then((r) => r.data)
      .catch(() => null), // never let a failed report block the UI lock

  result: (championshipId) =>
    firstOk([
      () => api.get(`/championship/${championshipId}/result`),
      () => api.get(`/championship/${championshipId}/results/me`),
    ]),

  leaderboard: (scope = "weekly") =>
    firstOk([
      () => api.get("/championship/leaderboard", { params: { scope } }),
      () => api.get("/leaderboard", { params: { scope } }),
    ]),
};

export default championshipApi;