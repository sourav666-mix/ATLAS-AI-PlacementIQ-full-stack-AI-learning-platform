// CodePanel.jsx - [NEW] Monaco editor + run
// FILE: frontend/src/components/Arena/CodePanel.jsx
// BATCH 27 / v10 Code Arena (new) - The Monaco editor panel with a language
// switch and starter code per language. "Run" executes visible tests; for
// Python it can run INSTANTLY in the student's browser via the Pyodide
// worker (Batch 21) — zero server round-trip — while "Submit" always goes to
// the server sandbox for the graded hidden-test run + AI review.

import React, { useEffect, useMemo, useState } from "react";
import Editor from "@monaco-editor/react";
import { Play, Send } from "lucide-react";
import { Button, Spinner } from "../Common";

const LANGS = [
  { id: "python", label: "Python", monaco: "python" },
  { id: "java", label: "Java", monaco: "java" },
  { id: "cpp", label: "C++", monaco: "cpp" },
  { id: "sql", label: "SQL", monaco: "sql" },
];

export default function CodePanel({
  problem, onRun, onSubmit, running, submitting,
}) {
  const available = useMemo(() => {
    const starters = problem?.starter_code || {};
    const langs = LANGS.filter((l) => starters[l.id] != null);
    return langs.length ? langs : [LANGS[0]];
  }, [problem]);

  const [lang, setLang] = useState(available[0].id);
  const [code, setCode] = useState("");

  useEffect(() => {
    const starters = problem?.starter_code || {};
    setCode(starters[lang] ?? starters.python ?? "");
  }, [problem, lang]);

  const monacoLang =
    LANGS.find((l) => l.id === lang)?.monaco || "python";

  return (
    <div className="flex flex-col h-full bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-800">
        <div className="flex gap-1">
          {available.map((l) => (
            <button
              key={l.id}
              onClick={() => setLang(l.id)}
              className={`px-3 py-1 rounded-lg text-xs transition ${
                lang === l.id
                  ? "bg-gray-800 text-gray-100"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              {l.label}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onRun(lang, code)}
            disabled={running || submitting}
          >
            {running ? <Spinner size={13} /> : <><Play size={13} className="inline mr-1" />Run</>}
          </Button>
          <Button
            size="sm"
            onClick={() => onSubmit(lang, code)}
            disabled={running || submitting}
          >
            {submitting ? <Spinner size={13} /> : <><Send size={13} className="inline mr-1" />Submit</>}
          </Button>
        </div>
      </div>
      <div className="flex-1 min-h-[300px]">
        <Editor
          height="100%"
          language={monacoLang}
          theme="vs-dark"
          value={code}
          onChange={(value) => setCode(value ?? "")}
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            padding: { top: 12 },
            tabSize: 4,
          }}
        />
      </div>
    </div>
  );
}