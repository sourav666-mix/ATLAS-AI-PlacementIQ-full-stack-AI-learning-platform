// FILE: frontend/src/components/LiveLab/ArtifactDownload.jsx
// BATCH 22 / v11 Phase 16 (new) - The artifact is REAL: the trained model
// (.pkl), chart PNGs, and cleaned CSVs live in Pyodide's virtual FS; this
// panel streams them out of the worker and onto the student's disk.
// Only NAME + SIZE metadata is reported to the backend (never the bytes).

import React, { useEffect, useState } from "react";
import labApi from "../../api/labApi";
import useLabStore from "../../store/labStore";

const ARTIFACT_EXT = /\.(pkl|joblib|png|jpg|csv|json|html|txt|onnx)$/i;

export default function ArtifactDownload({ pyodide }) {
  const { lab, datasetName } = useLabStore();
  const [artifacts, setArtifacts] = useState([]);

  useEffect(() => {
    if (pyodide.running || !pyodide.ready) return;
    pyodide
      .listFiles()
      .then((res) =>
        setArtifacts(
          (res.files || []).filter(
            (f) => ARTIFACT_EXT.test(f.name) && f.name !== datasetName
          )
        )
      )
      .catch(() => {});
  }, [pyodide.running, pyodide.ready, pyodide, datasetName]);

  const download = async (file) => {
    const res = await pyodide.readFile(file.name);
    if (res.error) return;
    const blob = new Blob([res.buffer]);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = file.name;
    a.click();
    URL.revokeObjectURL(url);
    // Metadata only — the artifact bytes never touch the backend
    if (lab) {
      const kind = file.name.match(/\.(pkl|joblib|onnx)$/i)
        ? "model"
        : file.name.match(/\.(png|jpg)$/i)
        ? "chart"
        : "data";
      labApi
        .grade(lab.id, {}, undefined, [
          { name: file.name, size_kb: file.sizeKb, kind },
        ])
        .catch(() => {});
    }
  };

  if (artifacts.length === 0) return null;

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-2">
      <h3 className="text-sm font-semibold text-gray-200">
        Your artifacts — download to disk
      </h3>
      <ul className="space-y-1">
        {artifacts.map((file) => (
          <li key={file.name} className="flex items-center justify-between text-xs">
            <span className="font-mono text-gray-300 truncate">
              {file.name}
              <span className="text-gray-600"> · {file.sizeKb} KB</span>
            </span>
            <button
              onClick={() => download(file)}
              className="px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-cyan-400"
            >
              ↓ download
            </button>
          </li>
        ))}
      </ul>
      <p className="text-[11px] text-gray-600">
        Trained a model? <span className="font-mono">import pickle;
        pickle.dump(model, open('model.pkl','wb'))</span> — then download it
        here. It reloads in any real Python environment.
      </p>
    </div>
  );
}