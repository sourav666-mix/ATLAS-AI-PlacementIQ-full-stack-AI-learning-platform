// useTextToSpeech.js - plays base64 TTS audio
// FILE: frontend/src/hooks/useTextToSpeech.js
// BATCH 28 / v10 Global Assistant + Studio (new) - Plays TTS audio. The
// backend returns base64 audio from the self-hosted Chatterbox endpoint
// (ElevenLabs fallback); this hook decodes and plays it. If a response
// comes back text-only (both TTS providers down), it degrades gracefully to
// the browser's built-in SpeechSynthesis so the assistant still speaks.

import { useCallback, useEffect, useRef, useState } from "react";

function base64ToBlob(base64, mime = "audio/mpeg") {
  const clean = base64.includes(",") ? base64.split(",")[1] : base64;
  const bytes = atob(clean);
  const buffer = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i += 1) buffer[i] = bytes.charCodeAt(i);
  return new Blob([buffer], { type: mime });
}

export default function useTextToSpeech() {
  const audioRef = useRef(null);
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setSpeaking(false);
  }, []);

  // Play base64 audio (mp3/wav) from Chatterbox/ElevenLabs.
  const playBase64 = useCallback((base64, mime = "audio/mpeg") => {
    stop();
    try {
      const url = URL.createObjectURL(base64ToBlob(base64, mime));
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => {
        setSpeaking(false);
        URL.revokeObjectURL(url);
      };
      audio.onerror = () => setSpeaking(false);
      setSpeaking(true);
      audio.play().catch(() => setSpeaking(false));
    } catch (_) {
      setSpeaking(false);
    }
  }, [stop]);

  // Fallback: browser SpeechSynthesis when no audio bytes were returned.
  const speakText = useCallback((text) => {
    if (typeof window === "undefined" || !window.speechSynthesis || !text) return;
    stop();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.onend = () => setSpeaking(false);
    setSpeaking(true);
    window.speechSynthesis.speak(utterance);
  }, [stop]);

  // Smart entry: prefer real audio bytes, else fall back to text synth.
  const speak = useCallback(({ audio, mime, text }) => {
    if (audio) playBase64(audio, mime || "audio/mpeg");
    else if (text) speakText(text);
  }, [playBase64, speakText]);

  return { speaking, speak, playBase64, speakText, stop };
}