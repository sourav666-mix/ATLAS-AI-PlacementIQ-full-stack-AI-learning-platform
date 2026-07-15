// vite.config.js - vite config
// FILE: frontend/vite.config.js — BATCH 24 (new)
// Pyodide worker (v11) needs the ES-module worker format; exclude the
// Monaco + Pyodide heavy deps from pre-bundling so dev start stays fast.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  worker: { format: "es" },
  optimizeDeps: { exclude: ["pyodide"] },
  server: { port: 5173 },
  build: { target: "es2020", chunkSizeWarningLimit: 1600 },
});
