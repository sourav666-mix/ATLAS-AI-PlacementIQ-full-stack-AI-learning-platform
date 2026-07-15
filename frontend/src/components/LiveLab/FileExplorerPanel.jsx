// frontend/src/components/LiveLab/FileExplorerPanel.jsx   [NEW v12]
// VS Code Explorer + Colab Files pane: tree over the virtual FS, drag-drop + Upload button,
// new file, rename, delete, download. Uploads write straight into Pyodide's FS — nothing is POSTed.
import { useMemo, useRef, useState } from "react";
import { useLiveLabStore } from "../../store/liveLabV2Store";
import { isBinaryName } from "../../utils/labKernel";

function buildTree(paths) {
  const root = {};
  for (const p of paths) {
    const parts = p.split("/");
    let node = root;
    parts.forEach((part, i) => {
      node[part] = node[part] || { __path: parts.slice(0, i + 1).join("/"), __leaf: i === parts.length - 1, children: {} };
      node = node[part].children;
    });
  }
  return root;
}

function Node({ node, name, kernel }) {
  const { openTab, deleteFile, renameFile, files } = useLiveLabStore();
  const [open, setOpen] = useState(true);
  const meta = files[node.__path];
  const isFolder = Object.keys(node.children).length > 0;

  const download = async () => {
    let bytes;
    if (meta?.isBinary) bytes = await kernel.readFile(node.__path);
    else bytes = new TextEncoder().encode(meta?.content ?? "");
    const url = URL.createObjectURL(new Blob([bytes]));
    const a = document.createElement("a");
    a.href = url; a.download = name; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="pl-2">
      <div className="group flex items-center gap-1 py-0.5 rounded hover:bg-zinc-800/60">
        <button
          onClick={() => (isFolder ? setOpen((o) => !o) : openTab(node.__path))}
          className="flex items-center gap-1.5 flex-1 text-left text-sm text-zinc-300 truncate"
        >
          <span className="text-zinc-500 w-3">{isFolder ? (open ? "▾" : "▸") : ""}</span>
          <span>{isFolder ? "📁" : meta?.isBinary ? "📊" : "📄"}</span>
          <span className="truncate">{name}</span>
        </button>
        {!isFolder && (
          <span className="opacity-0 group-hover:opacity-100 flex gap-1 pr-1">
            <button title="Download" onClick={download} className="text-xs text-zinc-500 hover:text-zinc-200">⭳</button>
            <button title="Rename" onClick={() => { const to = prompt("Rename to", node.__path); if (to) renameFile(node.__path, to); }} className="text-xs text-zinc-500 hover:text-zinc-200">✎</button>
            <button title="Delete" onClick={() => { deleteFile(node.__path); kernel.deleteFile?.(node.__path).catch(() => {}); }} className="text-xs text-zinc-500 hover:text-rose-400">✕</button>
          </span>
        )}
      </div>
      {isFolder && open && Object.entries(node.children).map(([n, c]) => <Node key={c.__path} node={c} name={n} kernel={kernel} />)}
    </div>
  );
}

export default function FileExplorerPanel({ kernel }) {
  const { files, createFile, registerUploaded, mergeFsPaths } = useLiveLabStore();
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);
  const tree = useMemo(() => buildTree(Object.keys(files)), [files]);

  const ingest = async (fileList) => {
    for (const file of fileList) {
      const path = file.name;
      if (isBinaryName(file.name)) {
        const buf = new Uint8Array(await file.arrayBuffer());
        await kernel.writeFile(path, buf); // straight into the virtual FS, never uploaded
        registerUploaded(path);
      } else {
        createFile(path, await file.text());
      }
    }
  };

  const refreshFromKernel = async () => {
    const entries = await kernel.listFiles("/home/pyodide");
    mergeFsPaths(entries.filter((e) => !e.isDir).map((e) => e.path.replace("/home/pyodide/", "")));
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => { e.preventDefault(); setDragOver(false); ingest(e.dataTransfer.files); }}
      className={`h-full flex flex-col border-r border-zinc-800 bg-zinc-950 ${dragOver ? "ring-2 ring-violet-500/60" : ""}`}
    >
      <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800">
        <span className="text-xs font-semibold uppercase tracking-wide text-zinc-400">Explorer</span>
        <div className="flex gap-2">
          <button title="New file" onClick={() => { const p = prompt("New file path", "notes.py"); if (p) createFile(p, ""); }} className="text-zinc-400 hover:text-zinc-100 text-sm">＋</button>
          <button title="Upload" onClick={() => inputRef.current?.click()} className="text-zinc-400 hover:text-zinc-100 text-sm">⭱</button>
          <button title="Refresh from kernel" onClick={refreshFromKernel} className="text-zinc-400 hover:text-zinc-100 text-sm">⟳</button>
        </div>
      </div>
      <input ref={inputRef} type="file" multiple hidden onChange={(e) => ingest(e.target.files)} />
      <div className="flex-1 overflow-y-auto py-1">
        {Object.entries(tree).map(([n, c]) => <Node key={c.__path} node={c} name={n} kernel={kernel} />)}
      </div>
      <p className="px-3 py-2 text-[11px] text-zinc-500 border-t border-zinc-800">🔒 Files stay on your device — nothing is uploaded.</p>
    </div>
  );
}