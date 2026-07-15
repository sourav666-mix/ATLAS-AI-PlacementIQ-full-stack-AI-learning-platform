// frontend/src/components/LabPro/FilesPanel.jsx
/**
 * ATLAS AI 4.0 - v12 Live Lab Pro: the Colab-style Files panel.
 *
 * Drag-and-drop uploads (CSV / Excel / JSON / images / .py) go straight
 * into the kernel's virtual filesystem - they stay on the student's
 * device and are NEVER sent to the backend. That privacy line is stated
 * in the UI on purpose: it is a real trust advantage over cloud
 * notebooks. Download pulls the (possibly modified) file back out of the
 * virtual FS as a Blob.
 */

import { useCallback, useState } from "react";
import kernel from "./labProKernel";

function prettySize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FilesPanel() {
  const [uploads, setUploads] = useState(kernel.uploads);
  const [dragOver, setDragOver] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);

  const ingest = useCallback(async (fileList) => {
    setBusy(true);
    setNotice(null);
    try {
      for (const file of Array.from(fileList)) {
        if (file.size > 60 * 1024 * 1024) {
          setNotice(`${file.name}: over 60 MB - too large for in-browser RAM.`);
          continue;
        }
        const buf = await file.arrayBuffer();
        const next = await kernel.writeUpload(file.name, buf);
        setUploads([...next]);
      }
    } catch (err) {
      setNotice(`Upload failed: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }, []);

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragOver(false);
      if (e.dataTransfer?.files?.length) ingest(e.dataTransfer.files);
    },
    [ingest]
  );

  const download = useCallback(async (name) => {
    try {
      const bytes = await kernel.readVirtualFile(name);
      const blob = new Blob([bytes]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setNotice(`Download failed: ${err.message}`);
    }
  }, []);

  const remove = useCallback((name) => {
    setUploads([...kernel.deleteUpload(name)]);
  }, []);

  return (
    <div className="flex h-full flex-col">
      <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-zinc-400">
        Files
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`mx-3 rounded-lg border-2 border-dashed p-4 text-center text-xs
                    ${dragOver ? "border-sky-500 bg-sky-950/30 text-sky-300"
                               : "border-zinc-700 text-zinc-500"}`}
      >
        {busy ? "Loading into the kernel…" : "Drag a CSV / Excel / JSON / .py here"}
        <div className="mt-1">
          <label className="cursor-pointer text-sky-400 hover:underline">
            or browse
            <input
              type="file"
              multiple
              className="hidden"
              onChange={(e) => e.target.files && ingest(e.target.files)}
            />
          </label>
        </div>
      </div>

      <ul className="mt-2 flex-1 overflow-auto px-3 text-sm">
        {uploads.map((u) => (
          <li key={u.name}
              className="group flex items-center justify-between rounded px-1 py-1 hover:bg-zinc-800">
            <span className="truncate text-zinc-200">
              {u.name}
              <span className="ml-2 text-xs text-zinc-500">{prettySize(u.size)}</span>
            </span>
            <span className="hidden gap-2 group-hover:flex">
              <button type="button" title="Download" onClick={() => download(u.name)}
                className="text-zinc-400 hover:text-sky-400">↓</button>
              <button type="button" title="Remove" onClick={() => remove(u.name)}
                className="text-zinc-400 hover:text-red-400">✕</button>
            </span>
          </li>
        ))}
        {uploads.length === 0 && (
          <li className="px-1 py-2 text-xs text-zinc-600">No files yet.</li>
        )}
      </ul>

      {notice && (
        <div className="mx-3 mb-2 rounded bg-amber-950/50 px-2 py-1 text-xs text-amber-300">
          {notice}
        </div>
      )}
      <div className="border-t border-zinc-800 px-3 py-2 text-[11px] leading-4 text-zinc-500">
        🔒 Your files never leave this browser tab - practice on sensitive
        data with zero upload risk.
      </div>
    </div>
  );
}