// frontend/src/hooks/usePyodideV2.js   [v12 — the Live Lab 2.0 kernel hook]
// Boots the v2 worker once per mount and exposes: status, runCode (with live
// streaming via onChunk), and path-based FS ops. The SAME kernel instance is
// passed down through LabWorkspace so every pane shares one session.
//
// NOTE: this is the v12 rebuild that was accidentally pasted over
// src/workers/pyodideWorker.js. It lives here now, and talks to its own worker
// (pyodideWorkerV2.js) — the v11 hook/worker pair (usePyodide.js) is untouched
// and still serves ArenaWorkspace/PyodideTest.
import { useCallback, useEffect, useRef, useState } from "react";

export function usePyodide() {
  const workerRef = useRef(null);
  const pending = useRef(new Map()); // id -> { resolve, reject, onChunk }
  const seq = useRef(0);
  const [status, setStatus] = useState("booting"); // booting | ready | running | error

  useEffect(() => {
    const worker = new Worker(new URL("../workers/pyodideWorkerV2.js", import.meta.url), { type: "module" });
    workerRef.current = worker;

    worker.onmessage = (e) => {
      const { id, type } = e.data;
      if (type === "ready") return setStatus("ready");
      if (type === "boot_error") return setStatus("error");

      if (type === "stream") {
        const p = pending.current.get(e.data.runId);
        p?.onChunk?.(e.data.stream, e.data.text);
        return;
      }
      const p = pending.current.get(id);
      if (!p) return;
      if (type === "result") p.resolve({ result: e.data.result });
      else if (type === "fs_ok") p.resolve({ path: e.data.path });
      else if (type === "fs_read") p.resolve({ data: e.data.data });
      else if (type === "fs_list") p.resolve({ entries: e.data.entries });
      else if (type === "error") p.reject(new Error(e.data.error));
      pending.current.delete(id);
    };

    return () => worker.terminate();
  }, []);

  const send = useCallback((type, payload = {}, onChunk) => {
    const id = `m${seq.current++}`;
    return new Promise((resolve, reject) => {
      pending.current.set(id, { resolve, reject, onChunk });
      workerRef.current.postMessage({ id, type, ...payload });
    });
  }, []);

  const runCode = useCallback(async (code, onChunk) => {
    setStatus("running");
    try {
      return await send("run", { code }, onChunk);
    } finally {
      setStatus("ready");
    }
  }, [send]);

  const writeFile = useCallback((path, data) => send("writeFile", { path, data }), [send]);
  const readFile = useCallback((path) => send("readFile", { path }).then((r) => r.data), [send]);
  const listFiles = useCallback((root) => send("listdir", { root }).then((r) => r.entries), [send]);
  const deleteFile = useCallback((path) => send("delete", { path }), [send]);
  const resetKernel = useCallback(() => send("reset"), [send]);

  return { status, ready: status !== "booting" && status !== "error", runCode, writeFile, readFile, listFiles, deleteFile, resetKernel };
}

export default usePyodide;
