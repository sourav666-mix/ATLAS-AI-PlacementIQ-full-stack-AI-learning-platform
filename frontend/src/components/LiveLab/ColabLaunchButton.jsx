// FILE: frontend/src/components/LiveLab/ColabLaunchButton.jsx
// BATCH 22 / v11 Phase 17 (new) - One-click free-GPU bridge: asks the
// backend for a ready-to-run notebook (student code + dataset loader +
// results callback), saves it as an .ipynb, and opens Colab. Zero platform
// GPU cost — the compute runs on Google's free tier.

import React, { useState } from "react";
import labApi from "../../api/labApi";
import useLabStore from "../../store/labStore";
import ColabResultModal from "./ColabResultModal";

export default function ColabLaunchButton() {
  const { lab, code } = useLabStore();
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState(null);

  if (!lab || !lab.needs_gpu) return null;

  const launch = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await labApi.colabLaunch(lab.id, code);
      const blob = new Blob([JSON.stringify(res.notebook, null, 1)], {
        type: "application/x-ipynb+json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = res.filename;
      a.click();
      URL.revokeObjectURL(url);
      window.open(res.open_url, "_blank", "noopener");
      setNote(res.note);
      setShowModal(true);
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message || err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="bg-gray-900 rounded-xl border border-amber-900/60 p-4 space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-amber-300">
          Deep learning? Free GPU bridge
        </h3>
      </div>
      <button
        onClick={launch}
        disabled={busy}
        className="w-full px-3 py-2 text-sm rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-40 text-gray-950 font-semibold"
      >
        {busy ? "Building notebook…" : "🚀 Launch on Colab GPU (free)"}
      </button>
      {note && <p className="text-[11px] text-gray-500">{note}</p>}
      {error && <p className="text-xs text-red-400">{error}</p>}
      {showModal && (
        <ColabResultModal onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}