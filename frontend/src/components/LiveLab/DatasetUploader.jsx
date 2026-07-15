// FILE: frontend/src/components/LiveLab/DatasetUploader.jsx
// BATCH 22 / v11 Phase 14 (new) - Drag-drop a CSV/Excel INTO THE BROWSER:
// the file is written to Pyodide's virtual filesystem so the student can
// pd.read_csv('name.csv') it. The file is NEVER POSTed anywhere — say it in
// the UI, it's a real trust advantage. Quick-look buttons run
// df.head()/info()/describe() locally.

import React, { useRef, useState } from "react";
import useLabStore from "../../store/labStore";

const ACCEPT = ".csv,.xlsx,.xls,.tsv,.json";
const MAX_MB = 100;

export default function DatasetUploader({ pyodide }) {
  const { datasetName, setDatasetName } = useLabStore();
  const [dragging, setDragging] = useState(false);
  const [sizeKb, setSizeKb] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const ingest = async (file) => {
    setError(null);
    if (!file) return;
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`File is ${(file.size / 1048576).toFixed(0)}MB — keep it under ${MAX_MB}MB for in-browser work.`);
      return;
    }
    try {
      const buffer = await file.arrayBuffer();
      const res = await pyodide.writeFile(file.name, buffer);
      setDatasetName(res.name);
      setSizeKb(res.sizeKb);
    } catch (err) {
      setError(String(err.message || err));
    }
  };

  const quickLook = (kind) => {
    if (!datasetName) return;
    const reader = datasetName.match(/\.(xlsx|xls)$/i)
      ? `pd.read_excel('${datasetName}')`
      : `pd.read_csv('${datasetName}')`;
    const body = {
      head: `print(df.head().to_string())`,
      info: `import io\nbuf = io.StringIO()\ndf.info(buf=buf)\nprint(buf.getvalue())`,
      describe: `print(df.describe(include='all').to_string())`,
    }[kind];
    pyodide.runCode(`import pandas as pd\ndf = ${reader}\n${body}`);
  };

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-3">
      <h3 className="text-sm font-semibold text-gray-200">Your dataset</h3>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          ingest(e.dataTransfer.files && e.dataTransfer.files[0]);
        }}
        onClick={() => inputRef.current && inputRef.current.click()}
        className={`cursor-pointer rounded-lg border-2 border-dashed px-4 py-6 text-center text-sm transition ${
          dragging
            ? "border-cyan-500 bg-cyan-950/30 text-cyan-300"
            : "border-gray-700 text-gray-500 hover:border-gray-500"
        }`}
      >
        {datasetName ? (
          <span className="text-gray-300">
            {datasetName} · {sizeKb ?? "?"} KB — loaded into your browser
          </span>
        ) : (
          <span>Drag a CSV / Excel here, or click to choose</span>
        )}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          onChange={(e) => ingest(e.target.files && e.target.files[0])}
        />
      </div>

      {datasetName && (
        <div className="flex gap-2">
          {["head", "info", "describe"].map((kind) => (
            <button
              key={kind}
              onClick={() => quickLook(kind)}
              disabled={!pyodide.ready || pyodide.running}
              className="flex-1 px-2 py-1.5 text-xs rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-40 text-gray-300"
            >
              df.{kind}()
            </button>
          ))}
        </div>
      )}
      {error && <p className="text-xs text-red-400">{error}</p>}
      <p className="text-[11px] text-gray-600">
        🔒 Stays on your machine. The file is written to an in-browser
        filesystem and is never uploaded — practice on sensitive data safely.
      </p>
    </div>
  );
}