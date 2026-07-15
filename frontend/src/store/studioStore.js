// frontend/src/store/studioStore.js
// BATCH 31 / v10 Interview Studio - Zustand store.
// Tracks the live session: current question, turn history, and the final
// report. InterviewStudio.jsx drives all API calls; this store just holds
// state between them.

import { create } from "zustand";

export const useStudioStore = create((set, get) => ({
  sessionId: null,
  domain: null,
  level: null,
  count: 0,
  index: 0,
  currentQuestion: null, // {text, audio, audio_mime}
  turns: [], // [{question, answer, score, feedback, model}]
  report: null,

  begin: ({ sessionId, domain, level, count, question }) =>
    set({
      sessionId,
      domain,
      level,
      count,
      index: 0,
      currentQuestion: question,
      turns: [],
      report: null,
    }),

  recordTurn: ({ answer, score, feedback, model, nextQuestion }) => {
    const { currentQuestion, turns, index } = get();
    set({
      turns: [...turns, { question: currentQuestion, answer, score, feedback, model }],
      index: index + 1,
      currentQuestion: nextQuestion || null,
    });
  },

  finish: (report) => set({ report }),

  reset: () =>
    set({
      sessionId: null,
      domain: null,
      level: null,
      count: 0,
      index: 0,
      currentQuestion: null,
      turns: [],
      report: null,
    }),
}));

export default useStudioStore;
