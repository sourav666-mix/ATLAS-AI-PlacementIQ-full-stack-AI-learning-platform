// GlobalAssistantPanel.jsx - [MOD] slide-in chat + voice panel
// FILE: frontend/src/components/GlobalAssistant/GlobalAssistantPanel.jsx
// BATCH 28 / v10 Global Assistant (new) - The chat panel: message list, a
// text input with a mic (Web Speech STT), and a voice toggle that speaks
// replies (Chatterbox/ElevenLabs base64 -> useTextToSpeech, with browser
// synth fallback). The current route is sent as source_page so the backend's
// injected context can be page-aware. The assistant is stateless server-side;
// history shown here is client-only.

import React, { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { Send, Mic, MicOff, Volume2, VolumeX, Sparkles } from "lucide-react";
import useTutorStore from "../../store/tutorStore";
import tutorGlobalApi from "../../api/tutorGlobalApi";
import useSpeechRecognition from "../../hooks/useSpeechRecognition";
import useTextToSpeech from "../../hooks/useTextToSpeech";
import { Spinner } from "../Common";

export default function GlobalAssistantPanel() {
  const {
    open, locked, voice, messages, setVoice, pushUser, pushAssistant,
  } = useTutorStore();
  const location = useLocation();
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const endRef = useRef(null);

  const stt = useSpeechRecognition();
  const tts = useTextToSpeech();

  // Push finalized speech into the input box
  useEffect(() => {
    if (stt.transcript) setInput(stt.transcript);
  }, [stt.transcript]);

  useEffect(() => {
    if (endRef.current) endRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  if (!open || locked) return null;

  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;
    if (stt.listening) stt.stop();
    setInput("");
    setError(null);
    pushUser(text);
    setBusy(true);
    try {
      const data = await tutorGlobalApi.chat({
        message: text,
        sourcePage: location.pathname,
        voice,
      });
      const reply =
        data.reply || data.message || data.answer || data.response || "";
      const audio = data.audio || data.audio_base64 || null;
      pushAssistant(reply, audio);
      if (voice) tts.speak({ audio, mime: data.audio_mime, text: reply });
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally {
      setBusy(false);
    }
  };

  const toggleMic = () => {
    if (stt.listening) stt.stop();
    else stt.start();
  };

  const toggleVoice = () => {
    if (voice) tts.stop();
    setVoice(!voice);
  };

  return (
    <div className="fixed bottom-24 right-5 z-40 w-[min(24rem,calc(100vw-2.5rem))] h-[32rem] flex flex-col bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-cyan-400" />
          <span className="text-sm font-semibold text-gray-100">
            ATLAS Assistant
          </span>
        </div>
        <button
          onClick={toggleVoice}
          title={voice ? "Voice on" : "Voice off"}
          className={`p-1.5 rounded-lg transition ${
            voice ? "text-cyan-400 bg-cyan-950/50" : "text-gray-500 hover:text-gray-300"
          }`}
        >
          {voice ? <Volume2 size={16} /> : <VolumeX size={16} />}
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-sm text-gray-500 mt-8 px-4">
            <p>Ask me anything — I already know your roadmap, your scores,
            and where you're stuck.</p>
            <p className="mt-2 text-xs text-gray-600">
              Try: "What should I practice next?"
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-sm leading-relaxed whitespace-pre-wrap ${
                m.role === "user"
                  ? "bg-cyan-600 text-white rounded-br-sm"
                  : "bg-gray-800 text-gray-200 rounded-bl-sm"
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-2xl rounded-bl-sm px-3.5 py-2.5">
              <Spinner size={14} />
            </div>
          </div>
        )}
        {error && <p className="text-xs text-red-400 text-center">{error}</p>}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-gray-800">
        {stt.listening && (
          <p className="text-[11px] text-cyan-400 mb-1.5 animate-pulse">
            Listening… {stt.interim}
          </p>
        )}
        <div className="flex items-end gap-2">
          {stt.supported && (
            <button
              onClick={toggleMic}
              title={stt.listening ? "Stop mic" : "Speak"}
              className={`shrink-0 h-9 w-9 rounded-lg flex items-center justify-center transition ${
                stt.listening
                  ? "bg-red-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:text-gray-200"
              }`}
            >
              {stt.listening ? <MicOff size={16} /> : <Mic size={16} />}
            </button>
          )}
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            rows={1}
            placeholder="Ask anything…"
            className="flex-1 resize-none bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-cyan-700 max-h-24"
          />
          <button
            onClick={send}
            disabled={busy || !input.trim()}
            className="shrink-0 h-9 w-9 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white flex items-center justify-center transition"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}