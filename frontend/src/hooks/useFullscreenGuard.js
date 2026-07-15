// useFullscreenGuard.js - [NEW] championship proctoring: fullscreen + tab-switch lock
// FILE: frontend/src/hooks/useFullscreenGuard.js
// BATCH 30 / v10 Championship (new) - The proctoring guard. Requests the
// Fullscreen API on start, then watches fullscreenchange + visibilitychange +
// window blur. The rules (System Understanding §9):
//   * one grace warning if the FIRST exit happens within the first 10 seconds
//   * any exit after that (or a second exit ever) => lock + auto-submit
// The server is the source of truth; this is the client half that reports the
// violation and forces submission. Nothing here decides the score.

import { useCallback, useEffect, useRef, useState } from "react";

const GRACE_MS = 10000;

export default function useFullscreenGuard({ active, onWarn, onLock }) {
  const startedAtRef = useRef(null);
  const usedGraceRef = useRef(false);
  const lockedRef = useRef(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const requestFullscreen = useCallback(async () => {
    const el = document.documentElement;
    try {
      if (el.requestFullscreen) await el.requestFullscreen();
      else if (el.webkitRequestFullscreen) await el.webkitRequestFullscreen();
      startedAtRef.current = Date.now();
      setIsFullscreen(true);
    } catch (_) {
      // Fullscreen can be blocked; the exam still runs but exits are stricter.
      startedAtRef.current = Date.now();
    }
  }, []);

  const exitFullscreen = useCallback(() => {
    try {
      if (document.fullscreenElement && document.exitFullscreen) {
        document.exitFullscreen();
      }
    } catch (_) {
      /* ignore */
    }
  }, []);

  const lock = useCallback(() => {
    if (lockedRef.current) return;
    lockedRef.current = true;
    exitFullscreen();
    if (onLock) onLock();
  }, [exitFullscreen, onLock]);

  useEffect(() => {
    if (!active) return undefined;

    const handleViolation = () => {
      if (!active || lockedRef.current) return;
      const withinGrace =
        startedAtRef.current &&
        Date.now() - startedAtRef.current < GRACE_MS;

      if (withinGrace && !usedGraceRef.current) {
        // First accidental exit in the opening seconds: one warning only.
        usedGraceRef.current = true;
        if (onWarn) onWarn();
        // Try to pull them back into fullscreen.
        requestFullscreen();
        return;
      }
      lock();
    };

    const onFsChange = () => {
      const fs = !!document.fullscreenElement;
      setIsFullscreen(fs);
      if (!fs) handleViolation();
    };
    const onVisibility = () => {
      if (document.visibilityState === "hidden") handleViolation();
    };
    const onBlur = () => handleViolation();

    document.addEventListener("fullscreenchange", onFsChange);
    document.addEventListener("webkitfullscreenchange", onFsChange);
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("blur", onBlur);

    return () => {
      document.removeEventListener("fullscreenchange", onFsChange);
      document.removeEventListener("webkitfullscreenchange", onFsChange);
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("blur", onBlur);
    };
  }, [active, lock, onWarn, requestFullscreen]);

  return { requestFullscreen, exitFullscreen, isFullscreen };
}