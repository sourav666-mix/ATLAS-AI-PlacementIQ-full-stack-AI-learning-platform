// tailwind.config.js - admin dark theme tokens
// FILE: admin-panel/tailwind.config.js — BATCH 32 (new)
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: { colors: { brand: { DEFAULT: "#a78bfa", dark: "#6d28d9" } } } },
  plugins: [],
};