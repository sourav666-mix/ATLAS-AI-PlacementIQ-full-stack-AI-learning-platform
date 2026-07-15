// FILE: frontend/src/pages/LiveLab.jsx
// BATCH 21 / v11 Phase 13 (new) - The Live Lab page: lab catalog (from
// GET /lab) -> open one lab -> the workspace. Domain-aware via ?domain_id=.

import React, { useEffect, useState } from "react";
import labApi from "../api/labApi";
import useLabStore from "../store/labStore";
import LabWorkspace from "../components/LiveLab/LabWorkspace";

const TYPE_BADGES = {
  ds: "Data Science", analysis: "Data Analysis", ml: "AI / ML",
  genai: "GenAI", mlops: "MLOps", cloud: "Cloud", cyber: "Cyber",
};

export default function LiveLab() {
  const { lab, setLab, reset } = useLabStore();
  const [labs, setLabs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    labApi
      .list(params.get("domain_id") || undefined)
      .then(setLabs)
      .catch((err) =>
        setError(String(err?.response?.data?.detail || err.message))
      )
      .finally(() => setLoading(false));
    return () => reset();
  }, [reset]);

  const openLab = async (labId) => {
    setError(null);
    try {
      setLab(await labApi.get(labId));
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-4 lg:p-6">
      {!lab ? (
        <div className="max-w-4xl mx-auto space-y-4">
          <div>
            <h1 className="text-2xl font-bold">Live Lab</h1>
            <p className="text-sm text-gray-400">
              Real Python — pandas, scikit-learn, matplotlib — running on
              YOUR machine. Your data never leaves your browser.
            </p>
          </div>
          {loading && <p className="text-gray-500">Loading labs…</p>}
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <div className="grid sm:grid-cols-2 gap-3">
            {labs.map((item) => (
              <button
                key={item.id}
                onClick={() => openLab(item.id)}
                className="text-left bg-gray-900 border border-gray-800 hover:border-cyan-700 rounded-xl p-4 transition"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-800 text-cyan-400">
                    {TYPE_BADGES[item.lab_type] || item.lab_type}
                  </span>
                  {item.needs_gpu && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-900 text-amber-300">
                      GPU bridge
                    </span>
                  )}
                </div>
                <h3 className="mt-2 font-semibold text-gray-100">
                  {item.title}
                </h3>
              </button>
            ))}
          </div>
          {!loading && labs.length === 0 && !error && (
            <p className="text-gray-500 text-sm">
              No labs published yet — run seed_labs.py on the backend.
            </p>
          )}
        </div>
      ) : (
        <div className="max-w-7xl mx-auto h-[calc(100vh-3rem)] flex flex-col gap-3">
          <button
            onClick={() => reset()}
            className="self-start text-xs text-gray-500 hover:text-gray-300"
          >
            ← All labs
          </button>
          <div className="flex-1 min-h-0">
            <LabWorkspace />
          </div>
        </div>
      )}
    </div>
  );
}