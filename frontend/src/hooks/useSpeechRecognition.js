// useSpeechRecognition.js - Web Speech API STT (Global Assistant + Studio)
// FILE: frontend/src/hooks/useSpeechRecognition.js
// BATCH 28 / v10 Global Assistant (new) - Web Speech API speech-to-text.
// FREE, in-browser, zero cost (Section 8). Exposes start/stop, a live
// transcript, listening state, and a `supported` flag so the UI can hide
// the mic where the browser lacks it (Firefox, some mobile browsers).

import { useCallback, useEffect, useRef, useState } from "react";

function getRecognition() {
  if (typeof window === "undefined") return null;
  const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition;
  return Ctor ? new Ctor() : null;
}

export default function useSpeechRecognition({ lang = "en-US" } = {}) {
  const recognitionRef = useRef(null);
  const [supported, setSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interim, setInterim] = useState("");

  useEffect(() => {
    const recognition = getRecognition();
    if (!recognition) {
      setSupported(false);
      return undefined;
    }
    setSupported(true);
    recognition.lang = lang;
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      let finalText = "";
      let interimText = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const chunk = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += chunk;
        else interimText += chunk;
      }
      if (finalText) setTranscript((prev) => (prev + " " + finalText).trim());
      setInterim(interimText);
    };
    recognition.onend = () => {
      setListening(false);
      setInterim("");
    };
    recognition.onerror = () => {
      setListening(false);
      setInterim("");
    };

    recognitionRef.current = recognition;
    return () => {
      try {
        recognition.stop();
      } catch (_) {
        /* already stopped */
      }
    };
  }, [lang]);

  const start = useCallback(() => {
    const recognition = recognitionRef.current;
    if (!recognition || listening) return;
    setTranscript("");
    setInterim("");
    try {
      recognition.start();
      setListening(true);
    } catch (_) {
      /* start() throws if already running — ignore */
    }
  }, [listening]);

  const stop = useCallback(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;
    try {
      recognition.stop();
    } catch (_) {
      /* ignore */
    }
    setListening(false);
  }, []);

  const reset = useCallback(() => {
    setTranscript("");
    setInterim("");
  }, []);

  return { supported, listening, transcript, interim, start, stop, reset };
}