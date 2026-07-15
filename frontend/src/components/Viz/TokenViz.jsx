// frontend/src/components/Viz/TokenViz.jsx
/**
 * ATLAS AI 4.0 - v12 viz pack: token_viz (LLM Basics / GenAI).
 * Type a sentence, watch it split into colored tokens with IDs, and see
 * the context-window meter fill - tokens, embeddings-as-IDs and context
 * limits in one toy. (Toy tokenizer: word pieces, deterministic IDs.)
 * Also serves prompt_viz and attention_viz-lite via VizMount aliases.
 */

import { useState } from "react";

const CONTEXT = 24;
const COLORS = ["#0ea5e9", "#22c55e", "#f59e0b", "#a78bfa", "#f472b6", "#2dd4bf"];

function tokenize(text) {
  // toy: split words; words > 6 chars split into two "pieces"
  const out = [];
  text.trim().split(/\s+/).filter(Boolean).forEach((word) => {
    if (word.length > 6) {
      out.push(word.slice(0, Math.ceil(word.length / 2)));
      out.push("##" + word.slice(Math.ceil(word.length / 2)));
    } else out.push(word);
  });
  return out;
}

const tokenId = (t) =>
  1000 + ([...t].reduce((a, c) => (a * 31 + c.charCodeAt(0)) % 8999, 7));

export default function TokenViz() {
  const [text, setText] = useState("Transformers predict the next token");
  const tokens = tokenize(text);
  const pct = Math.min(100, Math.round((tokens.length / CONTEXT) * 100));

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-xs">
      <input value={text} onChange={(e) => setText(e.target.value)}
        className="mb-2 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1
                   font-mono text-zinc-100 outline-none focus:border-sky-500"
        placeholder="type a sentence…" />

      <div className="flex flex-wrap gap-1">
        {tokens.map((t, i) => (
          <span key={i}
                title={`token id ${tokenId(t)}`}
                className="rounded px-1.5 py-0.5 font-mono text-zinc-950"
                style={{ background: COLORS[i % COLORS.length] }}>
            {t}
            <span className="ml-1 opacity-70">{tokenId(t)}</span>
          </span>
        ))}
        {tokens.length === 0 && <span className="text-zinc-600">no tokens yet</span>}
      </div>

      <div className="mt-2">
        <div className="flex justify-between text-zinc-500">
          <span>context window</span>
          <span className={pct >= 100 ? "text-red-400" : ""}>
            {tokens.length}/{CONTEXT} tokens{pct >= 100 ? " — FULL, oldest tokens fall out" : ""}
          </span>
        </div>
        <div className="mt-1 h-2 w-full rounded bg-zinc-800">
          <div className={`h-2 rounded ${pct >= 100 ? "bg-red-500" : "bg-sky-500"}`}
               style={{ width: `${pct}%` }} />
        </div>
      </div>
      <p className="mt-2 text-zinc-500">
        Long words split into pieces (##) - models read token IDs, never letters.
      </p>
    </div>
  );
}