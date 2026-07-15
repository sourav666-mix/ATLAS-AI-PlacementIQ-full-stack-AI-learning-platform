// studioApi.js - [NEW] start / turn / finish (voice interview)
// FILE: frontend/src/api/studioApi.js
// BATCH 31 / v10 Interview Studio (new) - start / turn / finish. start
// generates the question set once; each turn sends the transcript + presence
// NUMBERS (never frames) and gets evaluation + follow-up + next question;
// finish builds the report. voice_mode asks the server for TTS audio.

import api from "./axios";

const studioApi = {
  domains: () => api.get("/studio/domains").then((r) => r.data),

  start: ({ domain, level, count, voice = true }) =>
    api
      .post("/studio/start", { domain, level, question_count: count, voice_mode: voice })
      .then((r) => r.data),

  turn: ({ sessionId, answer, presence, voice = true }) =>
    api
      .post(`/studio/${sessionId}/turn`, {
        answer,
        presence_pct: presence?.presence_pct ?? null,
        look_aways: presence?.look_aways ?? 0,
        voice_mode: voice,
      })
      .then((r) => r.data),

  finish: ({ sessionId, presence }) =>
    api
      .post(`/studio/${sessionId}/finish`, {
        presence_pct: presence?.presence_pct ?? null,
        look_aways: presence?.look_aways ?? 0,
      })
      .then((r) => r.data),
};

export default studioApi;