// frontend/src/components/LiveLab/EditorTabs.jsx   [NEW v12]
// Multi-file tabbed Monaco editor (VS Code-style). Language is inferred per file.
import Editor from "@monaco-editor/react";
import { useLiveLabStore } from "../../store/liveLabV2Store";

export default function EditorTabs() {
  const { openTabs, activeTab, files, setActiveTab, closeTab, setFileContent } = useLiveLabStore();
  const active = activeTab ? files[activeTab] : null;

  return (
    <div className="flex flex-col h-full bg-zinc-950">
      <div className="flex items-stretch border-b border-zinc-800 overflow-x-auto">
        {openTabs.map((path) => (
          <div
            key={path}
            className={`group flex items-center gap-2 px-3 py-1.5 text-sm border-r border-zinc-800 cursor-pointer whitespace-nowrap ${
              activeTab === path ? "bg-zinc-900 text-zinc-100" : "text-zinc-400 hover:text-zinc-200"
            }`}
            onClick={() => setActiveTab(path)}
          >
            <span>{path.split("/").pop()}</span>
            {files[path]?.dirty && <span className="h-1.5 w-1.5 rounded-full bg-violet-400" />}
            <button onClick={(e) => { e.stopPropagation(); closeTab(path); }} className="opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-zinc-200">✕</button>
          </div>
        ))}
      </div>
      <div className="flex-1 min-h-0">
        {active && !active.isBinary ? (
          <Editor
            path={activeTab}
            theme="vs-dark"
            language={active.language}
            value={active.content ?? ""}
            onChange={(v) => setFileContent(activeTab, v ?? "")}
            options={{ minimap: { enabled: false }, fontSize: 14, scrollBeyondLastLine: false, automaticLayout: true, tabSize: 4 }}
          />
        ) : (
          <div className="h-full grid place-items-center text-zinc-500 text-sm">
            {active?.isBinary ? "Binary file — use it in code via its path." : "Open a file from the Explorer."}
          </div>
        )}
      </div>
    </div>
  );
}