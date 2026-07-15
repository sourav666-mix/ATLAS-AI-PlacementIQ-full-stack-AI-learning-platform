// tutorStore.js - Global Assistant open state + chat history
// FILE: frontend/src/store/tutorStore.js
// BATCH 28 / v10 Global Assistant (new) - open state + local chat history +
// the live-championship lock. History lives ONLY on the client for display;
// it is never sent back to the server (the assistant is stateless by design).

import { create } from "zustand";

const useTutorStore = create((set) => ({
  open: false,
  voice: false,
  locked: false,        // true during a live championship exam
  messages: [],         // [{role:'user'|'assistant', text, audio?}]

  toggle: () => set((s) => ({ open: !s.open })),
  close: () => set({ open: false }),
  setVoice: (voice) => set({ voice }),
  setLocked: (locked) => set((s) => ({ locked, open: locked ? false : s.open })),

  pushUser: (text) =>
    set((s) => ({ messages: [...s.messages, { role: "user", text }] })),
  pushAssistant: (text, audio) =>
    set((s) => ({
      messages: [...s.messages, { role: "assistant", text, audio }],
    })),
  clear: () => set({ messages: [] }),
}));

export default useTutorStore;