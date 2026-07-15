// FILE: frontend/src/workers/pyodideWorker.js
// BATCH 21 / v11 Phase 13 - Pyodide web worker (v11 protocol).
// RESTORED from the built asset after the file was accidentally overwritten by
// the v12 usePyodide hook. Serves the v11 hook (src/hooks/usePyodide.js) used
// by ArenaWorkspace / PyodideTest / PyodideRunner.
//
// Protocol (messages IN): init{cdn} | run{id,code} | runTests{id,tests}
//                         | writeFile{id,name,buffer} | readFile{id,name} | listFiles{id}
// Protocol (messages OUT): status{stage} | stdout/stderr{id,text} | figure{id,dataUrl}
//                         | done{id,ok,error,ms} | testResults{id,results,ms}
//                         | fileWritten | fileData | fileList | fatal{error}

const DEFAULT_CDN = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";
const PRELOAD_PACKAGES = ["pandas", "numpy", "scikit-learn", "matplotlib", "scipy"];

let pyodide = null;
let bootPromise = null;
let currentRunId = null;

const MPL_SETUP = `
import os, sys
os.environ.setdefault("MPLBACKEND", "AGG")
import matplotlib
matplotlib.use("AGG")

def _atlas_capture_figures():
    import base64, io
    import matplotlib.pyplot as plt
    payload = []
    for num in plt.get_fignums():
        fig = plt.figure(num)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=110)
        payload.append(base64.b64encode(buf.getvalue()).decode("ascii"))
    plt.close("all")
    return payload
`;

function post(msg) {
  self.postMessage(msg);
}

async function boot(cdn) {
  if (!bootPromise) {
    bootPromise = (async () => {
      post({ type: "status", stage: "loading-pyodide" });
      const base = cdn || DEFAULT_CDN;
      pyodide = await (await import(/* @vite-ignore */ base + "pyodide.mjs")).loadPyodide({
        indexURL: base,
      });
      post({ type: "status", stage: "loading-packages" });
      await pyodide.loadPackage(PRELOAD_PACKAGES);
      pyodide.setStdout({ batched: (text) => post({ type: "stdout", id: currentRunId, text }) });
      pyodide.setStderr({ batched: (text) => post({ type: "stderr", id: currentRunId, text }) });
      await pyodide.runPythonAsync(MPL_SETUP);
      post({ type: "status", stage: "ready" });
    })();
  }
  return bootPromise;
}

async function flushFigures(id) {
  try {
    const proxy = pyodide.runPython("_atlas_capture_figures()");
    const figures = proxy.toJs ? proxy.toJs() : proxy;
    if (proxy.destroy) proxy.destroy();
    for (const b64 of figures) {
      post({ type: "figure", id, dataUrl: "data:image/png;base64," + b64 });
    }
  } catch {
    /* figures are best-effort */
  }
}

async function run(id, code) {
  await boot();
  currentRunId = id;
  const started = performance.now();
  try {
    await pyodide.loadPackagesFromImports(code);
    await pyodide.runPythonAsync(code);
    await flushFigures(id);
    post({ type: "done", id, ok: true, ms: Math.round(performance.now() - started) });
  } catch (err) {
    await flushFigures(id);
    post({
      type: "done",
      id,
      ok: false,
      error: String(err && err.message ? err.message : err),
      ms: Math.round(performance.now() - started),
    });
  } finally {
    currentRunId = null;
  }
}

async function runTests(id, tests) {
  await boot();
  currentRunId = null;
  const started = performance.now();
  const results = {};
  for (const t of tests || []) {
    try {
      await pyodide.runPythonAsync(t.test_code || "raise AssertionError()");
      results[t.id] = true;
    } catch {
      results[t.id] = false;
    }
  }
  post({ type: "testResults", id, results, ms: Math.round(performance.now() - started) });
}

function writeFile(id, name, buffer) {
  const safeName = String(name).split("/").pop().split("\\").pop();
  pyodide.FS.writeFile(safeName, new Uint8Array(buffer));
  post({ type: "fileWritten", id, name: safeName, sizeKb: Math.round(buffer.byteLength / 1024) });
}

function readFile(id, name) {
  try {
    const data = pyodide.FS.readFile(String(name));
    post({ type: "fileData", id, name, buffer: data.buffer }, [data.buffer]);
  } catch (err) {
    post({ type: "fileData", id, name, error: String(err) });
  }
}

function listFiles(id) {
  const files = pyodide.FS.readdir(".")
    .filter((f) => f !== "." && f !== ".." && !f.startsWith("__"))
    .map((f) => {
      try {
        const stat = pyodide.FS.stat(f);
        return { name: f, sizeKb: Math.round(stat.size / 1024) };
      } catch {
        return { name: f, sizeKb: 0 };
      }
    });
  post({ type: "fileList", id, files });
}

self.onmessage = async (event) => {
  const msg = event.data || {};
  try {
    switch (msg.type) {
      case "init":
        await boot(msg.cdn);
        break;
      case "run":
        await run(msg.id, msg.code || "");
        break;
      case "runTests":
        await runTests(msg.id, msg.tests);
        break;
      case "writeFile":
        await boot();
        writeFile(msg.id, msg.name, msg.buffer);
        break;
      case "readFile":
        readFile(msg.id, msg.name);
        break;
      case "listFiles":
        listFiles(msg.id);
        break;
      default:
        break;
    }
  } catch (err) {
    post({ type: "fatal", error: String(err && err.message ? err.message : err) });
  }
};
