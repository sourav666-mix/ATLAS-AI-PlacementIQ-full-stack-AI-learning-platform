// vite.config.js - admin vite config
// FILE: admin-panel/vite.config.js — BATCH 32 (new)
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  server: { port: 5174 }, // student app is 5173; admin is 5174
  build: { target: "es2020" },
});