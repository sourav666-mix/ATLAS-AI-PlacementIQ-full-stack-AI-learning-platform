// FILE: frontend/src/hooks/usePyodide.js
// BATCH 21 / v11 Phase 13 (new) - React hook around the Pyodide worker.
// Boots the worker once (module-level singleton — the ~15MB Pyodide load
// happens ONE time per tab, not per component), exposes:
//   runCode(src) -> Promise<{ok, error, ms}>
//   runTests(tests) -> Promise<{results, ms}>   (deterministic grading)
//   writeFile(name, arrayBuffer), readFile(name), listFiles()
//   status: 'idle'|'loading-pyodide'|'loading-packages'|'ready'|'fatal'
//   output: [{kind:'stdout'|'stderr'|'figure'|'system', text?, dataUrl?}]

import { useCallback, useEffect, useRef, useState } from "react";

let sharedWorker = null;
let seq = 0;
const pending = new Map(); // id -> {resolve, kind}
const listeners = new Set(); // per-hook message listeners

function getWorker() {
  if (!sharedWorker) {
    sharedWorker = new Worker(
      new URL("../workers/pyodideWorker.js", import.meta.url),
      { type: "module" }
    );
    sharedWorker.onmessage = (event) => {
      const msg = event.data || {};
      const waiter = msg.id != null ? pending.get(msg.id) : null;
      if (waiter) {
        if (msg.type === "done" && waiter.kind === "run") {
          pending.delete(msg.id);
          waiter.resolve({ ok: msg.ok, error: msg.error, ms: msg.ms });
        } else if (msg.type === "testResults" && waiter.kind === "tests") {
          pending.delete(msg.id);
          waiter.resolve({ results: msg.results, ms: msg.ms });
        } else if (
          ["fileWritten", "fileData", "fileList"].includes(msg.type) &&
          waiter.kind === "file"
        ) {
          pending.delete(msg.id);
          waiter.resolve(msg);
        }
      }
      listeners.forEach((fn) => fn(msg));
    };
    sharedWorker.postMessage({
      type: "init",
      cdn: import.meta.env.VITE_PYODIDE_CDN || undefined,
    });
  }
  return sharedWorker;
}

function request(kind, payload) {
  const id = ++seq;
  return new Promise((resolve) => {
    pending.set(id, { resolve, kind });
    getWorker().postMessage({ ...payload, id });
  });
}

export default function usePyodide() {
  const [status, setStatus] = useState("idle");
  const [running, setRunning] = useState(false);
  const [output, setOutput] = useState([]);
  const statusRef = useRef(status);
  statusRef.current = status;

  useEffect(() => {
    const onMessage = (msg) => {
      if (msg.type === "status") setStatus(msg.stage);
      if (msg.type === "fatal") {
        setStatus("fatal");
        setOutput((prev) => [
          ...prev,
          { kind: "stderr", text: "Worker crashed: " + msg.error },
        ]);
      }
      if (msg.type === "stdout" || msg.type === "stderr") {
        setOutput((prev) => [...prev, { kind: msg.type, text: msg.text }]);
      }
      if (msg.type === "figure") {
        setOutput((prev) => [...prev, { kind: "figure", dataUrl: msg.dataUrl }]);
      }
    };
    listeners.add(onMessage);
    getWorker(); // ensure boot starts on first mount
    return () => listeners.delete(onMessage);
  }, []);

  const runCode = useCallback(async (code) => {
    setRunning(true);
    setOutput((prev) => [...prev, { kind: "system", text: ">>> run" }]);
    const result = await request("run", { type: "run", code });
    if (!result.ok && result.error) {
      setOutput((prev) => [...prev, { kind: "stderr", text: result.error }]);
    }
    setOutput((prev) => [
      ...prev,
      { kind: "system", text: `--- ${result.ok ? "ok" : "error"} in ${result.ms}ms` },
    ]);
    setRunning(false);
    return result;
  }, []);

  const runTests = useCallback(
    (tests) => request("tests", { type: "runTests", tests }),
    []
  );
  const writeFile = useCallback(
    (name, buffer) => request("file", { type: "writeFile", name, buffer }),
    []
  );
  const readFile = useCallback(
    (name) => request("file", { type: "readFile", name }),
    []
  );
  const listFiles = useCallback(
    () => request("file", { type: "listFiles" }),
    []
  );
  const clearOutput = useCallback(() => setOutput([]), []);

  return {
    status,
    ready: status === "ready",
    running,
    output,
    clearOutput,
    runCode,
    runTests,
    writeFile,
    readFile,
    listFiles,
  };
}