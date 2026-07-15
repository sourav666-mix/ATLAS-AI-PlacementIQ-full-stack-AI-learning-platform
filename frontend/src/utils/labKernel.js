// frontend/src/utils/labKernel.js   [NEW v12]
// Pure helpers shared by the Live Lab: matplotlib capture, output parsing, language mapping.
// No React, no network — just the glue that makes inline charts + Monaco languages work.

export const FIG_SENTINEL = "ATLAS_IMG::";

// Run ONCE when the kernel is ready. Forces the Agg backend (headless) and defines the
// figure flusher we call after every run to stream charts back as base64 PNGs.
export const KERNEL_INIT = `
import sys
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import io, base64
    def _atlas_flush_figs():
        for num in plt.get_fignums():
            fig = plt.figure(num)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=110)
            buf.seek(0)
            print("${FIG_SENTINEL}" + base64.b64encode(buf.read()).decode())
        plt.close("all")
except Exception:
    def _atlas_flush_figs():
        pass
`;

// Call this right after a user run to emit any figures produced during it.
export const CAPTURE_CALL = "_atlas_flush_figs()";

// Split raw stdout into visible text + captured images.
export function parseOutput(raw = "") {
  const images = [];
  const lines = [];
  for (const line of raw.split("\n")) {
    if (line.startsWith(FIG_SENTINEL)) images.push("data:image/png;base64," + line.slice(FIG_SENTINEL.length));
    else lines.push(line);
  }
  return { text: lines.join("\n").replace(/\n+$/, ""), images };
}

const EXT_LANG = {
  py: "python", js: "javascript", jsx: "javascript", ts: "typescript",
  json: "json", md: "markdown", markdown: "markdown", sql: "sql",
  html: "html", css: "css", csv: "plaintext", txt: "plaintext", yml: "yaml", yaml: "yaml",
};

export function languageForPath(path = "") {
  const ext = path.split(".").pop()?.toLowerCase() || "";
  return EXT_LANG[ext] || "plaintext";
}

export const isBinaryName = (name = "") =>
  /\.(csv|xlsx|xls|png|jpg|jpeg|gif|pkl|parquet|zip|npz|npy)$/i.test(name);