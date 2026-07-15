// tutorGlobalApi.js - global-chat (voice + context)
// FILE: frontend/src/api/tutorGlobalApi.js
// BATCH 28 / v10 Global Assistant (new) - POST /tutor/global-chat. Context
// is injected SERVER-SIDE from the user's token — the client only sends the
// message, the current page (so answers can be page-aware), and whether
// voice output is wanted. Never sends chat history: the assistant has no
// memory; context is assembled fresh every message (System Understanding).

import api from "./axios";

const tutorGlobalApi = {
  chat: ({ message, sourcePage, voice = false }) =>
    api
      .post("/tutor/global-chat", {
        message,
        source_page: sourcePage,
        voice_mode: voice,
      })
      .then((r) => r.data),
};

export default tutorGlobalApi;