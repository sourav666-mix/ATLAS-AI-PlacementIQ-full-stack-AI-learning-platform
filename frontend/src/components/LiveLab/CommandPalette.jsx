// frontend/src/components/LiveLab/CommandPalette.jsx   [NEW v12]
// ⌘K / Ctrl-K command palette — the pro touch that makes the lab feel like VS Code.
import { useEffect, useMemo, useState } from "react";

export default function CommandPalette({ commands }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setOpen((o) => !o); }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const filtered = useMemo(
    () => commands.filter((c) => c.label.toLowerCase().includes(q.toLowerCase())),
    [commands, q]
  );

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-start justify-center pt-32" onClick={() => setOpen(false)}>
      <div className="w-full max-w-lg rounded-xl border border-zinc-700 bg-zinc-900 shadow-2xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <input
          autoFocus value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="Type a command…"
          className="w-full bg-transparent px-4 py-3 text-zinc-100 outline-none border-b border-zinc-800"
        />
        <div className="max-h-72 overflow-y-auto">
          {filtered.map((c) => (
            <button
              key={c.label}
              onClick={() => { c.run(); setOpen(false); setQ(""); }}
              className="w-full flex items-center justify-between px-4 py-2.5 text-left text-sm text-zinc-200 hover:bg-violet-600/20"
            >
              <span>{c.label}</span>
              {c.hint && <span className="text-xs text-zinc-500">{c.hint}</span>}
            </button>
          ))}
          {!filtered.length && <p className="px-4 py-3 text-sm text-zinc-500">No commands</p>}
        </div>
      </div>
    </div>
  );
}