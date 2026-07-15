// FILE: frontend/src/components/SkillPath/VisualizationBlock.jsx
// v12 — renders visualization_config_json. Pure SVG/HTML, zero external libraries.
import React from "react";

export default function VisualizationBlock({ config }) {
  if (!config || !config.type) return null;
  const { type, params = [], data = [] } = config;

  return (
    <section className="rounded-xl border border-gray-800 bg-gray-900 p-5">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-violet-400">
        Visualization
      </h3>
      <div className="mt-3">
        {type === "flow_diagram" && (
          <div className="flex flex-wrap items-center gap-2">
            {(params.length ? params : ["Input", "Process", "Output"]).map((step, i, arr) => (
              <div key={i} className="flex items-center">
                <div className="rounded-lg border border-violet-500/40 bg-violet-500/10 px-4 py-2 text-sm text-violet-100">
                  {typeof step === "string" ? step : step.label}
                </div>
                {i < arr.length - 1 && <span className="mx-2 text-gray-600">→</span>}
              </div>
            ))}
          </div>
        )}

        {type === "table" && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <tbody>
                {(data.length ? data : params).map((row, i) => (
                  <tr key={i} className="border-b border-gray-800">
                    {(Array.isArray(row) ? row : Object.values(row)).map((cell, j) => (
                      <td key={j} className="px-3 py-2 text-gray-300">
                        {String(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {type === "code_trace" && (
          <pre className="rounded-lg bg-gray-950 border border-gray-800 p-4 text-sm text-emerald-300 overflow-x-auto whitespace-pre-wrap">
            {Array.isArray(params) ? params.join("\n") : String(params)}
          </pre>
        )}

        {type !== "flow_diagram" && type !== "table" && type !== "code_trace" && (
          <p className="text-sm text-gray-500">Visualization type: {type}</p>
        )}
      </div>
    </section>
  );
}