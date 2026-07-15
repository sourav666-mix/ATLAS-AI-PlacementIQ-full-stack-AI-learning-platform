// FILE: frontend/src/components/LiveLab/PyodideRunner.js
// BATCH 21 / v11 Phase 13 (new) - Thin client wrapper named per the folder
// structure: the ONE place components go to reach the shared Pyodide worker
// (via the usePyodide hook). Re-exported here so LiveLab components import
// from the LiveLab family, and so non-hook code can post to the worker.

import usePyodide from "../../hooks/usePyodide";

export const PYODIDE_PACKAGES = [
  "pandas",
  "numpy",
  "scikit-learn",
  "matplotlib",
  "scipy",
];

export const STATUS_LABELS = {
  idle: "Starting engine…",
  "loading-pyodide": "Loading Python (WebAssembly)…",
  "loading-packages": "Loading pandas · numpy · scikit-learn · matplotlib…",
  ready: "Python ready — runs on YOUR machine",
  fatal: "Engine crashed — reload the page",
};

export { usePyodide };
export default usePyodide;