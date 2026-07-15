// examStore.js - [NEW] live championship state (locked, timer, answers)
// FILE: frontend/src/store/examStore.js
// BATCH 30 / v10 Championship (new) - Live exam state: the paper, the current
// question, autosaved answers, the SERVER deadline (epoch ms), and locked.
// The countdown shown to the student is derived from the server deadline, not
// a local counter — the server still rejects late submits regardless.

import { create } from "zustand";

const useExamStore = create((set, get) => ({
  championshipId: null,
  title: "",
  questions: [],        // [{type, question, options?, ...}]
  answers: {},          // { [index]: answer }
  current: 0,
  deadlineMs: null,     // server entry_timestamp + duration
  locked: false,
  submitted: false,
  result: null,

  begin: ({ championshipId, title, questions, deadlineMs }) =>
    set({
      championshipId,
      title,
      questions,
      answers: {},
      current: 0,
      deadlineMs,
      locked: false,
      submitted: false,
      result: null,
    }),

  setAnswer: (index, value) =>
    set((s) => ({ answers: { ...s.answers, [index]: value } })),

  goTo: (index) =>
    set((s) => ({
      current: Math.max(0, Math.min(s.questions.length - 1, index)),
    })),
  next: () => get().goTo(get().current + 1),
  prev: () => get().goTo(get().current - 1),

  setLocked: (locked) => set({ locked }),
  setSubmitted: (result) => set({ submitted: true, result: result || null }),

  reset: () =>
    set({
      championshipId: null, title: "", questions: [], answers: {},
      current: 0, deadlineMs: null, locked: false, submitted: false, result: null,
    }),
}));

export default useExamStore;