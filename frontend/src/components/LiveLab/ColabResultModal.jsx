// FILE: frontend/src/components/LiveLab/ColabResultModal.jsx
// BATCH 22 / v11 Phase 17 (new) - Waits for the notebook's results callback.
// The Colab notebook's last cell POSTs the passed tasks to /lab/grade with
// the student's token; this modal polls GET /lab/{id} until the session's
// tasks_passed changes, then updates the checklist and celebrates.

import React, { useEffect, useRef, useState } from "react";
import labApi from "../../api/labApi";
import useLabStore from "../../store/labStore";

const POLL_MS = 15000;

export default function ColabResultModal({ onClose }) {
  const { lab, setTaskResults } = useLabStore();
  const [status, setStatus] = useState("waiting"); // waiting | received
  const [checks, setChecks] = useState(0);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!lab) return undefined;
    const baseline = JSON.stringify(
      (lab.session && lab.session.tasks_passed) || {}
    );
    const poll = async () => {
      try {
        const fresh = await labApi.get(lab.id);
        const now = (fresh.session && fresh.session.tasks_passed) || {};
        setChecks((c) => c + 1);
        if (JSON.stringify(now) !== baseline &&
            Object.values(now).some(Boolean)) {
          setTaskResults(now);
          setStatus("received");
          clearInterval(timerRef.current);
        }
      } catch (_) {
        /* transient network — keep polling */
      }
    };
    timerRef.current = setInterval(poll, POLL_MS);
    return () => clearInterval(timerRef.current);
  }, [lab, setTaskResults]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 max-w-md w-full space-y-4">
        {status === "waiting" ? (
          <>
            <h3 className="text-lg font-semibold text-gray-100">
              Training on Colab…
            </h3>
            <ol className="text-sm text-gray-400 list-decimal list-inside space-y-1">
              <li>In Colab: File → Upload notebook → pick the downloaded file</li>
              <li>Runtime → Change runtime type → <b>T4 GPU</b></li>
              <li>Run all cells; the last cell asks for your ATLAS token</li>
              <li>Copy it from Settings → API token in your dashboard</li>
            </ol>
            <p className="text-xs text-gray-500">
              Listening for your results… (checked {checks}×, every 15s)
            </p>
          </>
        ) : (
          <>
            <h3 className="text-lg font-semibold text-emerald-400">
              🎉 GPU results received!
            </h3>
            <p className="text-sm text-gray-300">
              Your Colab run reported back — the graded tasks are ticked.
              Close this and hit <b>Finish lab</b> to claim your points.
            </p>
          </>
        )}
        <button
          onClick={onClose}
          className="w-full px-3 py-2 text-sm rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200"
        >
          {status === "received" ? "Back to the lab" : "I'll check later"}
        </button>
      </div>
    </div>
  );
}