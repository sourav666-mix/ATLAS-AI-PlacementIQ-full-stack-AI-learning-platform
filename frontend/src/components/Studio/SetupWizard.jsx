// SetupWizard.jsx - [NEW] domain/level/count picker
// FILE: frontend/src/components/Studio/SetupWizard.jsx
// BATCH 31 / v10 Interview Studio (new) - The 3-choice setup: domain (16+),
// level, length. Also states the privacy rule plainly (camera = pressure +
// on-device numbers only, nothing stored) because that's a trust selling point.

import React, { useEffect, useState } from "react";
import { Camera, ShieldCheck } from "lucide-react";
import studioApi from "../../api/studioApi";
import { Button, Spinner } from "../Common";

const LEVELS = ["Beginner", "Intermediate", "Advanced"];
const LENGTHS = [3, 10, 15, 20];

export default function SetupWizard({ onStart, starting }) {
  const [domains, setDomains] = useState(null); // [{slug, name}] from the backend catalog
  const [domain, setDomain] = useState(null); // slug
  const [level, setLevel] = useState("Intermediate");
  const [count, setCount] = useState(3);

  useEffect(() => {
    studioApi.domains()
      .then((data) => {
        const list = data.domains || [];
        setDomains(list);
        setDomain(list[0]?.slug ?? null);
      })
      .catch(() => setDomains([]));
  }, []);

  return (
    <div className="space-y-6">
      <section className="rise space-y-3" style={{ "--d": "0ms" }}>
        <h2 className="text-sm font-semibold text-gray-300">1 · Domain</h2>
        {!domains ? (
          <div className="py-6 flex justify-center"><Spinner /></div>
        ) : (
          <div className="grid sm:grid-cols-3 lg:grid-cols-4 gap-2">
            {domains.map((d) => (
              <button
                key={d.slug}
                onClick={() => setDomain(d.slug)}
                className={`text-left rounded-xl border px-3 py-2.5 text-xs transition ${
                  domain === d.slug
                    ? "border-cyan-600 bg-cyan-950/30 text-cyan-200"
                    : "border-gray-800 bg-gray-900 text-gray-300 hover:border-gray-600"
                }`}
              >
                {d.name}
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="rise space-y-3" style={{ "--d": "80ms" }}>
        <h2 className="text-sm font-semibold text-gray-300">2 · Level</h2>
        <div className="flex gap-2">
          {LEVELS.map((l) => (
            <button
              key={l}
              onClick={() => setLevel(l)}
              className={`px-4 py-2 rounded-xl border text-sm transition ${
                level === l
                  ? "border-cyan-600 bg-cyan-950/30 text-cyan-200"
                  : "border-gray-800 bg-gray-900 text-gray-300 hover:border-gray-600"
              }`}
            >
              {l}
            </button>
          ))}
        </div>
      </section>

      <section className="rise space-y-3" style={{ "--d": "160ms" }}>
        <h2 className="text-sm font-semibold text-gray-300">3 · Length</h2>
        <div className="flex gap-2">
          {LENGTHS.map((n) => (
            <button
              key={n}
              onClick={() => setCount(n)}
              className={`px-4 py-2 rounded-xl border text-sm transition ${
                count === n
                  ? "border-cyan-600 bg-cyan-950/30 text-cyan-200"
                  : "border-gray-800 bg-gray-900 text-gray-300 hover:border-gray-600"
              }`}
            >
              {n} {n === 3 ? "(warm-up)" : "questions"}
            </button>
          ))}
        </div>
      </section>

      <div className="rise rounded-2xl border border-gray-800 bg-gray-900 p-4 flex items-start gap-3" style={{ "--d": "240ms" }}>
        <ShieldCheck size={18} className="text-emerald-400 shrink-0 mt-0.5" />
        <p className="text-xs text-gray-400 leading-relaxed">
          Your camera turns on to create real interview pressure. <b className="text-gray-300">Video is never recorded or uploaded</b> —
          only presence numbers (how often your face is in frame) are computed on your device and sent as plain numbers. You answer by voice; the interviewer speaks back.
        </p>
      </div>

      <div className="rise" style={{ "--d": "320ms" }}>
        <Button size="lg" onClick={() => onStart({ domain, level, count })} disabled={starting || !domain}>
          <Camera size={16} className="inline mr-2" />
          {starting ? "Starting…" : "Start interview"}
        </Button>
      </div>
    </div>
  );
}