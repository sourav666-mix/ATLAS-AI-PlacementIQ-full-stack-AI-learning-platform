// FILE: frontend/src/components/LiveLab/ResourcePanel.jsx
// BATCH 22 / v11 Phase 14 (new) - RAM/ROM awareness (v11 Guide §7): shows
// device memory (navigator.deviceMemory, Chrome), the estimated in-memory
// footprint of the loaded dataset (pandas typically needs ~3-5x the file
// size), a PRE-TRAIN warning when the footprint is large relative to the
// device, and the sizes of produced artifacts after a run. Pure client-side.

import React, { useCallback, useEffect, useState } from "react";
import useLabStore from "../../store/labStore";

const PANDAS_FACTOR = 4; // conservative in-RAM multiplier for a loaded CSV

export default function ResourcePanel({ pyodide }) {
  const { datasetName } = useLabStore();
  const [files, setFiles] = useState([]);
  const deviceGb =
    typeof navigator !== "undefined" && navigator.deviceMemory
      ? navigator.deviceMemory
      : null;

  const refresh = useCallback(async () => {
    if (!pyodide.ready) return;
    try {
      const res = await pyodide.listFiles();
      setFiles(res.files || []);
    } catch (_) {
      /* worker busy — fine */
    }
  }, [pyodide]);

  // Refresh the file list whenever a run finishes
  useEffect(() => {
    if (!pyodide.running) refresh();
  }, [pyodide.running, refresh]);

  const dataset = files.find((f) => f.name === datasetName);
  const footprintMb = dataset
    ? ((dataset.sizeKb * PANDAS_FACTOR) / 1024).toFixed(1)
    : null;
  const deviceMb = deviceGb ? deviceGb * 1024 : null;
  const heavy =
    dataset && deviceMb
      ? dataset.sizeKb * PANDAS_FACTOR > deviceMb * 1024 * 0.2 // >20% of RAM
      : false;

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-200">
          Resources — your machine
        </h3>
        <button
          onClick={refresh}
          className="text-xs text-gray-500 hover:text-gray-300"
        >
          refresh
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-gray-950 rounded-lg p-2 border border-gray-800">
          <p className="text-gray-500">Device RAM</p>
          <p className="text-gray-200 font-mono">
            {deviceGb ? `~${deviceGb} GB` : "unknown (non-Chrome)"}
          </p>
        </div>
        <div className="bg-gray-950 rounded-lg p-2 border border-gray-800">
          <p className="text-gray-500">Dataset footprint (est.)</p>
          <p className="text-gray-200 font-mono">
            {footprintMb ? `~${footprintMb} MB in RAM` : "no dataset yet"}
          </p>
        </div>
      </div>

      {heavy && (
        <p className="text-xs rounded-lg bg-amber-950/60 border border-amber-900 text-amber-300 p-2">
          ⚠ This dataset is large for your device. Sample it before training:
          <span className="font-mono"> df = df.sample(20000)</span>
        </p>
      )}

      {files.length > 0 && (
        <div className="text-xs">
          <p className="text-gray-500 mb-1">Files in your lab workspace:</p>
          <ul className="space-y-0.5 max-h-24 overflow-y-auto">
            {files.map((f) => (
              <li key={f.name} className="flex justify-between text-gray-400">
                <span className="font-mono truncate">{f.name}</span>
                <span className="text-gray-600">{f.sizeKb} KB</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}