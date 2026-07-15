// frontend/src/components/LabPro/labProKernel.js
/**
 * ATLAS AI 4.0 - v12 Live Lab Pro: the ONE kernel.
 *
 * A singleton adapter over two lazily loaded, CDN-served engines:
 *   python -> Pyodide (the student's CPU; pandas/numpy/matplotlib wheels)
 *   sql    -> sql.js (SQLite compiled to WASM - the MySQL practice subset)
 *
 * Design rules (locked):
 *   - ZERO npm dependencies: both engines load from CDN <script> tags at
 *     first use, so a CDN hiccup can never white-screen the app
 *     (v11 lesson: guard or remove optional deps).
 *   - One kernel per tab: notebook mode, workspace mode and the practice
 *     arena all share this module, so switching surfaces never loses
 *     variables or uploaded files.
 *   - Everything runs locally; uploaded files go into the virtual FS and
 *     NEVER leave the browser. Charts come back as data-URLs for inline
 *     display only - the backend's text-only guard strips them on save.
 */

const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/";
const SQLJS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.2/";

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
      if (existing.dataset.loaded === "1") return resolve();
      existing.addEventListener("load", resolve);
      existing.addEventListener("error", reject);
      return;
    }
    const s = document.createElement("script");
    s.src = src;
    s.async = true;
    s.addEventListener("load", () => {
      s.dataset.loaded = "1";
      resolve();
    });
    s.addEventListener("error", () =>
      reject(new Error(`Failed to load ${src}`))
    );
    document.head.appendChild(s);
  });
}

// Python bootstrap: capture stdout/stderr, render matplotlib to base64.
const PY_PRELUDE = `
import sys, io, base64, traceback
def _atlas_run(_src):
    _out = io.StringIO()
    _old_out, _old_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = _out
    _img = None
    try:
        _g = globals()
        try:
            _code = compile(_src, "<cell>", "eval")
            _val = eval(_code, _g)
            if _val is not None:
                print(repr(_val))
        except SyntaxError:
            exec(compile(_src, "<cell>", "exec"), _g)
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            if plt.get_fignums():
                _buf = io.BytesIO()
                plt.gcf().savefig(_buf, format="png", dpi=110,
                                  bbox_inches="tight")
                plt.close("all")
                _img = base64.b64encode(_buf.getvalue()).decode()
        except Exception:
            pass
        return {"ok": True, "text": _out.getvalue(), "image": _img}
    except Exception:
        return {"ok": False, "text": _out.getvalue()
                + traceback.format_exc(), "image": None}
    finally:
        sys.stdout, sys.stderr = _old_out, _old_err
`;

class LabProKernel {
  constructor() {
    this.pyodide = null;
    this.sqlDb = null;
    this.status = "cold"; // cold | loading | ready | error
    this.listeners = new Set();
    this.uploads = []; // [{name, size}] - metadata for the Files panel
  }

  onStatus(fn) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  _setStatus(s) {
    this.status = s;
    this.listeners.forEach((fn) => fn(s));
  }

  // ------------------------------ python -------------------------------

  async ensurePython() {
    if (this.pyodide) return this.pyodide;
    this._setStatus("loading");
    try {
      await loadScript(`${PYODIDE_CDN}pyodide.js`);
      this.pyodide = await window.loadPyodide({ indexURL: PYODIDE_CDN });
      await this.pyodide.runPythonAsync(PY_PRELUDE);
      this._setStatus("ready");
      return this.pyodide;
    } catch (err) {
      this._setStatus("error");
      throw err;
    }
  }

  async runPython(source) {
    const py = await this.ensurePython();
    try {
      await py.loadPackagesFromImports(source);
    } catch {
      /* unknown imports -> let the run surface the real error */
    }
    const runner = py.globals.get("_atlas_run");
    const result = runner(source);
    const out = result.toJs({ dict_converter: Object.fromEntries });
    result.destroy();
    return {
      ok: !!out.ok,
      text: out.text || "",
      image: out.image ? `data:image/png;base64,${out.image}` : null,
    };
  }

  /** Drag-dropped file -> Pyodide virtual FS. LOCAL ONLY, never uploaded. */
  async writeUpload(name, arrayBuffer) {
    const py = await this.ensurePython();
    py.FS.writeFile(name, new Uint8Array(arrayBuffer));
    this.uploads = [
      ...this.uploads.filter((u) => u.name !== name),
      { name, size: arrayBuffer.byteLength },
    ];
    return this.uploads;
  }

  async readVirtualFile(name) {
    const py = await this.ensurePython();
    return py.FS.readFile(name); // Uint8Array -> caller makes a Blob
  }

  deleteUpload(name) {
    if (this.pyodide) {
      try {
        this.pyodide.FS.unlink(name);
      } catch {
        /* already gone */
      }
    }
    this.uploads = this.uploads.filter((u) => u.name !== name);
    return this.uploads;
  }

  /** Sync workspace .py files into the FS so main.py can import utils.py. */
  async syncWorkspace(files) {
    const py = await this.ensurePython();
    for (const f of files) {
      if (f.is_folder) {
        try {
          py.FS.mkdirTree(f.path);
        } catch {
          /* exists */
        }
      }
    }
    for (const f of files) {
      if (!f.is_folder && f.path.endsWith(".py")) {
        const dir = f.path.includes("/")
          ? f.path.slice(0, f.path.lastIndexOf("/"))
          : "";
        if (dir) {
          try {
            py.FS.mkdirTree(dir);
          } catch {
            /* exists */
          }
        }
        py.FS.writeFile(f.path, f.content ?? "");
      }
    }
    // fresh import cache so re-runs pick up edited modules
    await py.runPythonAsync(
      "import importlib\nimportlib.invalidate_caches()"
    );
  }

  // -------------------------------- sql --------------------------------

  async ensureSql() {
    if (this.sqlDb) return this.sqlDb;
    this._setStatus("loading");
    try {
      await loadScript(`${SQLJS_CDN}sql-wasm.js`);
      const SQL = await window.initSqlJs({
        locateFile: (f) => `${SQLJS_CDN}${f}`,
      });
      this.sqlDb = new SQL.Database(); // persists for the tab's lifetime
      this._setStatus("ready");
      return this.sqlDb;
    } catch (err) {
      this._setStatus("error");
      throw err;
    }
  }

  async runSql(source) {
    const db = await this.ensureSql();
    try {
      const results = db.exec(source); // runs multiple ; statements
      if (!results.length) return { ok: true, text: "OK (no rows)", image: null };
      const parts = results.map(({ columns, values }) => {
        const widths = columns.map((c, i) =>
          Math.max(
            String(c).length,
            ...values.map((row) => String(row[i] ?? "NULL").length)
          )
        );
        const line = (cells) =>
          cells.map((c, i) => String(c ?? "NULL").padEnd(widths[i])).join("  ");
        return [
          line(columns),
          line(widths.map((w) => "-".repeat(w))),
          ...values.map(line),
          `(${values.length} row${values.length === 1 ? "" : "s"})`,
        ].join("\n");
      });
      return { ok: true, text: parts.join("\n\n"), image: null };
    } catch (err) {
      return { ok: false, text: String(err.message || err), image: null };
    }
  }

  // ------------------------------ dispatch ------------------------------

  async run(env, source) {
    if (!source || !source.trim())
      return { ok: true, text: "", image: null };
    return env === "sql" ? this.runSql(source) : this.runPython(source);
  }
}

/** THE singleton - notebook, workspace and practice arena all share it. */
export const kernel = new LabProKernel();
export default kernel;