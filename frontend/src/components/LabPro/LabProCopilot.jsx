// frontend/src/components/LabPro/LabProCopilot.jsx
/**
 * ATLAS AI 4.0 - v12 Live Lab Pro: the copilot panel.
 *
 * explain / suggest / fix / review over whatever the student is looking
 * at (active cell or active file). Fixes are shown with a copy button -
 * NEVER auto-applied, so they keep learning. The panel surfaces the two
 * cost signals honestly: a "cached - free" badge and the remaining daily
 * count; a 429 renders the friendly cap message from the backend.
 */

import { useCallback, useState } from "react";
import useLabProStore from "../../store/labProStore";
import labProApi from "../../api/labProApi";

const ACTIONS = [
  { key: "explain", label: "Explain" },
  { key: "suggest", label: "Next step" },
  { key: "fix", label: "Fix" },
  { key: "review", label: "Review" },
];

export default function LabProCopilot() {
  const { session, cells, runtimeOutputs, activeTab, fileContents } =
    useLabProStore();
  const [result, setResult] = useState(null);
  const [busyAction, setBusyAction] = useState(null);
  const [notice, setNotice] = useState(null);

  const currentContext = useCallback(() => {
    if (session?.mode === "workspace" && activeTab) {
      return { code: fileContents[activeTab] ?? "", errorText: null };
    }
    // notebook mode: last code cell + its output (tracebacks ride along)
    const codeCells = cells.filter((c) => c.cell_type === "code" && c.source.trim());
    const last = codeCells[codeCells.length - 1];
    if (!last) return { code: "", errorText: null };
    const out = runtimeOutputs[last.id];
    return {
      code: last.source,
      errorText: out && out.ok === false ? out.text.slice(0, 8000) : null,
    };
  }, [session, cells, runtimeOutputs, activeTab, fileContents]);

  const ask = useCallback(
    async (action) => {
      const { code, errorText } = currentContext();
      if (!code.trim()) {
        setNotice("Write some code first - the copilot needs context.");
        return;
      }
      setBusyAction(action);
      setNotice(null);
      try {
        const res = await labProApi.copilot({
          action,
          code,
          errorText,
          env: session?.active_env || "python",
        });
        setResult(res);
      } catch (err) {
        setResult(null);
        setNotice(
          err?.response?.status === 429
            ? err.response.data.detail
            : `Copilot unavailable: ${err?.response?.data?.detail || err.message}`
        );
      } finally {
        setBusyAction(null);
      }
    },
    [currentContext, session]
  );

  const copyFix = useCallback(() => {
    if (result?.fixed_code && navigator?.clipboard) {
      navigator.clipboard.writeText(result.fixed_code);
      setNotice("Fixed code copied - paste it where you want it.");
    }
  }, [result]);

  return (
    <div className="flex h-full flex-col rounded-lg border border-zinc-800 bg-zinc-900/60">
      <div className="flex items-center justify-between px-3 py-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
          AI Copilot
        </span>
        {result && (
          <span className="text-[11px] text-zinc-500">
            {result.cached ? (
              <span className="text-emerald-400">cached · free</span>
            ) : (
              <>left today: {result.remaining_today}</>
            )}
          </span>
        )}
      </div>

      <div className="flex gap-2 px-3 pb-2">
        {ACTIONS.map((a) => (
          <button
            key={a.key}
            type="button"
            disabled={busyAction !== null}
            onClick={() => ask(a.key)}
            className="rounded bg-zinc-800 px-2 py-1 text-xs text-zinc-200
                       hover:bg-sky-700 disabled:opacity-50"
          >
            {busyAction === a.key ? "…" : a.label}
          </button>
        ))}
      </div>

      <div className="flex-1 space-y-3 overflow-auto px-3 pb-3 text-sm">
        {result && (
          <>
            <p className="whitespace-pre-wrap text-zinc-200">{result.explanation}</p>
            {result.suggestion && (
              <p className="rounded bg-sky-950/40 px-2 py-1 text-sky-300">
                💡 {result.suggestion}
              </p>
            )}
            {result.fixed_code && (
              <div>
                <pre className="overflow-auto rounded bg-zinc-950 p-2 font-mono text-xs text-emerald-300">
                  {result.fixed_code}
                </pre>
                <button type="button" onClick={copyFix}
                  className="mt-1 text-xs text-sky-400 hover:underline">
                  Copy fix (you apply it - the copilot never edits for you)
                </button>
              </div>
            )}
          </>
        )}
        {!result && !notice && (
          <p className="text-xs text-zinc-600">
            The copilot reads your current cell or file - ask it to explain
            an error, suggest the next step, propose a fix, or review your
            approach.
          </p>
        )}
        {notice && (
          <p className="rounded bg-amber-950/50 px-2 py-1 text-xs text-amber-300">
            {notice}
          </p>
        )}
      </div>
    </div>
  );
}