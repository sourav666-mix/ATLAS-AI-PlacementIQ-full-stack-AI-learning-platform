// FILE: frontend/src/components/LiveLab/PyodideTest.jsx
// BATCH 21 / v11 Phase 13 (new) - THE proof component (Build Guide Session
// 10: "the make-or-break moment of the whole project"). Renders one button;
// clicking it runs real pandas in the browser and prints the version.
// Watch the Network tab while it runs: ZERO calls to your backend.
// Mount it temporarily on any route to verify, then remove.

import React from "react";
import usePyodide from "../../hooks/usePyodide";
import { STATUS_LABELS } from "./PyodideRunner";
import ConsoleOutput from "./ConsoleOutput";

const PROOF_CODE = `import sys
import pandas as pd
import numpy as np
import sklearn
import matplotlib
print("Python", sys.version.split()[0], "running IN YOUR BROWSER")
print("pandas", pd.__version__)
print("numpy", np.__version__)
print("scikit-learn", sklearn.__version__)
print("matplotlib", matplotlib.__version__)

import matplotlib.pyplot as plt
plt.plot([1, 2, 3, 4], [1, 4, 9, 16], marker="o")
plt.title("Rendered by matplotlib inside a Web Worker")
`;

export default function PyodideTest() {
  const pyodide = usePyodide();

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-4 bg-gray-950 min-h-screen">
      <h1 className="text-xl font-bold text-gray-100">
        Pyodide Proof — Session 10
      </h1>
      <p className="text-sm text-gray-400">
        {STATUS_LABELS[pyodide.status] || pyodide.status}
      </p>
      <button
        onClick={() => pyodide.runCode(PROOF_CODE)}
        disabled={!pyodide.ready || pyodide.running}
        className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white font-semibold"
      >
        {pyodide.running ? "Running…" : "Run pandas in my browser"}
      </button>
      <div className="h-96">
        <ConsoleOutput output={pyodide.output} onClear={pyodide.clearOutput} />
      </div>
    </div>
  );
}
