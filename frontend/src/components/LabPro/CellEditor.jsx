// frontend/src/components/LabPro/CellEditor.jsx
/**
 * ATLAS AI 4.0 - v12 Live Lab Pro: the shared cell/file editor.
 *
 * Dependency-free by design (spec: zero new npm packages) - a monospace
 * textarea with the two behaviours every surface relies on:
 *   * Shift+Enter -> onRun (notebook cells, workspace files, practice arena)
 *   * Tab inserts spaces instead of moving focus (4 for python, 2 otherwise)
 * Grows with content from a minRows floor; language only tunes tab width
 * and the aria-label, no highlighting here.
 */

import { useCallback } from "react";

export default function CellEditor({
  value,
  onChange,
  onRun,
  language = "python",
  minRows = 4,
  placeholder = "",
}) {
  const tab = language === "python" ? "    " : "  ";

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === "Enter" && e.shiftKey && onRun) {
        e.preventDefault();
        onRun();
        return;
      }
      if (e.key === "Tab") {
        e.preventDefault();
        const el = e.target;
        const { selectionStart: start, selectionEnd: end } = el;
        const next = value.slice(0, start) + tab + value.slice(end);
        onChange(next);
        // restore the caret after React re-renders the controlled value
        requestAnimationFrame(() => {
          el.selectionStart = el.selectionEnd = start + tab.length;
        });
      }
    },
    [value, onChange, onRun, tab]
  );

  const rows = Math.max(minRows, (value || "").split("\n").length);

  return (
    <textarea
      value={value}
      rows={rows}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={handleKeyDown}
      spellCheck={false}
      autoCapitalize="off"
      autoCorrect="off"
      aria-label={`${language} editor`}
      className="w-full resize-y rounded-md border border-zinc-800 bg-zinc-950
                 px-3 py-2 font-mono text-sm leading-relaxed text-zinc-200
                 placeholder:text-zinc-600 focus:border-sky-600 focus:outline-none"
    />
  );
}
