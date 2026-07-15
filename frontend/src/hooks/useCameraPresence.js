// useCameraPresence.js - [NEW] studio on-device face-present % (numbers only, no frames)
// FILE: frontend/src/hooks/useCameraPresence.js
// BATCH 31 / v10 Interview Studio (new) - Camera presence, computed ENTIRELY
// on-device. THE PRIVACY RULE (System Understanding §10): video is never
// uploaded and never recorded. This hook opens getUserMedia for a mirror
// preview and samples frames only into an in-memory canvas to compute two
// numbers — face-present % and long-look-away count — which are the ONLY
// things that ever leave the browser. No frame, blob, or dataURL is sent
// anywhere; the canvas is local and discarded each tick.

import { useCallback, useEffect, useRef, useState } from "react";

const SAMPLE_MS = 1200;      // how often we check presence
const LOOKAWAY_TICKS = 4;    // consecutive absent samples => a "long look-away"

export default function useCameraPresence() {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const canvasRef = useRef(null);
  const detectorRef = useRef(null);
  const timerRef = useRef(null);

  const samplesRef = useRef(0);
  const presentRef = useRef(0);
  const absentRunRef = useRef(0);
  const lookAwaysRef = useRef(0);

  const [active, setActive] = useState(false);
  const [error, setError] = useState(null);
  const [presencePct, setPresencePct] = useState(100);
  const [facePresent, setFacePresent] = useState(true);

  // Prepare a native FaceDetector if the browser has one (Chrome flag / some
  // mobile). Otherwise we fall back to a luminance-variance heuristic: a face
  // in frame produces far more mid-tone variance than an empty/dark frame.
  const detectPresence = useCallback(async () => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return false;

    if (detectorRef.current) {
      try {
        const faces = await detectorRef.current.detect(video);
        return faces && faces.length > 0;
      } catch (_) {
        detectorRef.current = null; // fall through to heuristic
      }
    }

    // Heuristic fallback — sample the centre region only.
    const canvas = canvasRef.current || document.createElement("canvas");
    canvasRef.current = canvas;
    const w = 64, h = 48;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    try {
      ctx.drawImage(video, 0, 0, w, h);
      const { data } = ctx.getImageData(w * 0.25, h * 0.2, w * 0.5, h * 0.6);
      let sum = 0, sumSq = 0, n = 0;
      for (let i = 0; i < data.length; i += 4) {
        const lum = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
        sum += lum; sumSq += lum * lum; n += 1;
      }
      const mean = sum / n;
      const variance = sumSq / n - mean * mean;
      // A present face: reasonable brightness + meaningful texture variance.
      return mean > 25 && mean < 245 && variance > 180;
    } catch (_) {
      return false;
    }
  }, []);

  const tick = useCallback(async () => {
    const present = await detectPresence();
    samplesRef.current += 1;
    if (present) {
      presentRef.current += 1;
      absentRunRef.current = 0;
    } else {
      absentRunRef.current += 1;
      if (absentRunRef.current === LOOKAWAY_TICKS) lookAwaysRef.current += 1;
    }
    setFacePresent(present);
    setPresencePct(
      Math.round((presentRef.current / samplesRef.current) * 100)
    );
  }, [detectPresence]);

  const start = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: 320, height: 240 },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => {});
      }
      if (typeof window !== "undefined" && "FaceDetector" in window) {
        try {
          // eslint-disable-next-line no-undef
          detectorRef.current = new window.FaceDetector({ fastMode: true });
        } catch (_) {
          detectorRef.current = null;
        }
      }
      samplesRef.current = 0;
      presentRef.current = 0;
      absentRunRef.current = 0;
      lookAwaysRef.current = 0;
      setActive(true);
      timerRef.current = setInterval(tick, SAMPLE_MS);
    } catch (err) {
      setError(
        "Camera permission is needed for the interview. You can still answer by voice — enable the camera for the full experience."
      );
    }
  }, [tick]);

  const stop = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setActive(false);
  }, []);

  useEffect(() => () => stop(), [stop]);

  // Only numbers. Never a frame.
  const getSignals = useCallback(
    () => ({
      presence_pct: samplesRef.current
        ? Math.round((presentRef.current / samplesRef.current) * 100)
        : null,
      look_aways: lookAwaysRef.current,
    }),
    []
  );

  return { videoRef, active, error, presencePct, facePresent, start, stop, getSignals };
}