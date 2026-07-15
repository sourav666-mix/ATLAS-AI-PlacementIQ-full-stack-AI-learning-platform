// frontend/src/workers/pyodideWorkerV2.js   [NEW v12 — Live Lab 2.0 kernel worker]
// Serves usePyodideV2.js. Self-boots on load (no init message needed).
//
// Protocol (messages IN):  run{id,code} | writeFile{id,path,data} | readFile{id,path}
//                          | listdir{id,root} | delete{id,path} | reset{id}
// Protocol (messages OUT): ready | boot_error{error}
//                          | stream{runId,stream:'stdout'|'stderr',text}   (live, during a run)
//                          | result{id,result} | fs_ok{id,path} | fs_read{id,data}
//                          | fs_list{id,entries:[{path,isDir}]} | error{id,error}

const DEFAULT_CDN = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";
const HOME = "/home/pyodide";

let pyodide = null;
let currentRunId = null;
const queue = []; // messages that arrive while booting

function post(msg, transfer) {
  self.postMessage(msg, transfer || []);
}

const bootPromise = (async () => {
  try {
    const base =
      (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_PYODIDE_CDN) ||
      DEFAULT_CDN;
    const { loadPyodide } = await import(/* @vite-ignore */ base + "pyodide.mjs");
    pyodide = await loadPyodide({ indexURL: base });
    pyodide.setStdout({
      batched: (text) => post({ type: "stream", runId: currentRunId, stream: "stdout", text: text + "\n" }),
    });
    pyodide.setStderr({
      batched: (text) => post({ type: "stream", runId: currentRunId, stream: "stderr", text: text + "\n" }),
    });
    post({ type: "ready" });
  } catch (err) {
    post({ type: "boot_error", error: String(err && err.message ? err.message : err) });
    throw err;
  }
})();

// resolve a path relative to the pyodide home dir
function absPath(p) {
  const s = String(p || "");
  return s.startsWith("/") ? s : `${HOME}/${s}`;
}

function mkdirsFor(path) {
  const parts = path.split("/").slice(0, -1);
  let cur = "";
  for (const part of parts) {
    if (!part) continue;
    cur += "/" + part;
    try {
      pyodide.FS.mkdir(cur);
    } catch {
      /* exists */
    }
  }
}

function walk(root, out) {
  let names;
  try {
    names = pyodide.FS.readdir(root);
  } catch {
    return;
  }
  for (const name of names) {
    if (name === "." || name === ".." || name.startsWith("__")) continue;
    const full = `${root}/${name}`.replace(/\/+/g, "/");
    let isDir = false;
    try {
      isDir = pyodide.FS.isDir(pyodide.FS.stat(full).mode);
    } catch {
      continue;
    }
    out.push({ path: full, isDir });
    if (isDir) walk(full, out);
  }
}

async function handleRun(id, code) {
  currentRunId = id;
  try {
    await pyodide.loadPackagesFromImports(code);
    const result = await pyodide.runPythonAsync(code);
    post({ type: "result", id, result: result === undefined || result === null ? null : String(result) });
  } catch (err) {
    post({ type: "error", id, error: String(err && err.message ? err.message : err) });
  } finally {
    currentRunId = null;
  }
}

const RESET_SNIPPET = `
import sys as _sys
_keep = {"__name__", "__doc__", "__package__", "__loader__", "__spec__", "__builtins__"}
for _k in list(globals().keys()):
    if _k not in _keep and not _k.startswith("_atlas"):
        del globals()[_k]
del _sys, _keep
`;

async function handle(msg) {
  const { id, type } = msg;
  try {
    switch (type) {
      case "run":
        await handleRun(id, msg.code || "");
        break;
      case "writeFile": {
        const path = absPath(msg.path);
        mkdirsFor(path);
        const data = msg.data instanceof Uint8Array ? msg.data : new Uint8Array(msg.data);
        pyodide.FS.writeFile(path, data);
        post({ type: "fs_ok", id, path: msg.path });
        break;
      }
      case "readFile": {
        const data = pyodide.FS.readFile(absPath(msg.path)); // Uint8Array
        post({ type: "fs_read", id, data }, [data.buffer]);
        break;
      }
      case "listdir": {
        const entries = [];
        walk(msg.root || HOME, entries);
        post({ type: "fs_list", id, entries });
        break;
      }
      case "delete":
        pyodide.FS.unlink(absPath(msg.path));
        post({ type: "fs_ok", id, path: msg.path });
        break;
      case "reset":
        await pyodide.runPythonAsync(RESET_SNIPPET);
        post({ type: "result", id, result: null });
        break;
      default:
        post({ type: "error", id, error: `unknown message type: ${type}` });
    }
  } catch (err) {
    post({ type: "error", id, error: String(err && err.message ? err.message : err) });
  }
}

self.onmessage = (event) => {
  const msg = event.data || {};
  if (pyodide) {
    handle(msg);
  } else {
    // buffer until boot completes so early sends (e.g. eager writeFile) don't drop
    queue.push(msg);
    bootPromise.then(() => {
      while (queue.length) handle(queue.shift());
    }).catch(() => {
      while (queue.length) {
        const m = queue.shift();
        post({ type: "error", id: m.id, error: "kernel failed to boot" });
      }
    });
  }
};
