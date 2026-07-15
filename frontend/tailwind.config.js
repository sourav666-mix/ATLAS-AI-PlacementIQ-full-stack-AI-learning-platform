// tailwind.config.js - [MOD] dark theme tokens (unchanged palette)
// FILE: frontend/tailwind.config.js — BATCH 24 (new) - dark theme.
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: { brand: { DEFAULT: "#22d3ee", dark: "#0e7490" } },
    },
  },
  plugins: [],
};