// InterviewStudio.jsx - [NEW] voice+camera live interviewer
// FILE: frontend/src/pages/InterviewStudio.jsx
// BATCH 31 / v10 Interview Studio (new) - /studio. The flagship live loop:
// setup -> for each turn { interviewer speaks (TTS) -> student answers (STT) ->
// submit transcript + presence numbers -> spoken+written feedback -> next Q }
// -> final report. Camera presence is on-device numbers only (never frames).
// REPLACES the Placeholder route target from Batch 24.

import React, { useCallback, useEffect, useState } from "react";
import { Mic, MicOff, Send, SkipForward } from "lucide-react";
import studioApi from "../api/studioApi";
import useStudioStore from "../store/studioStore";
import useCameraPresence from "../hooks/useCameraPresence";
import useSpeechRecognition from "../hooks/useSpeechRecognition";
import useTextToSpeech from "../hooks/useTextToSpeech";
import SetupWizard from "../components/Studio/SetupWizard";
import CameraTile from "../components/Studio/CameraTile";
import InterviewerAvatar from "../components/Studio/InterviewerAvatar";
import LiveSubtitles from "../components/Studio/LiveSubtitles";
import FinalReport from "../components/Studio/FinalReport";
import { Button, Spinner } from "../components/Common";

export default function InterviewStudio() {
  const [phase, setPhase] = useState("setup"); // setup | live | report
  const [starting, setStarting] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [typed, setTyped] = useState("");
  const [error, setError] = useState(null);

  const studio = useStudioStore();
  const camera = useCameraPresence();
  const stt = useSpeechRecognition();
  const tts = useTextToSpeech();

  const speakQuestion = useCallback(
    (question) => {
      if (question?.audio || question?.text) {
        tts.speak({ audio: question.audio, mime: question.audio_mime, text: question.text });
      }
    },
    [tts]
  );

  const start = async ({ domain, level, count }) => {
    setStarting(true);
    setError(null);
    try {
      await camera.start(); // best-effort; interview continues without it
      const data = await studioApi.start({ domain, level, count, voice: true });
      const question =
        data.question ||
        { text: data.question_text || data.first_question, audio: data.audio };
      studio.begin({
        sessionId: data.session_id || data.id,
        domain, level, count,
        question,
      });
      setPhase("live");
      speakQuestion(question);
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally {
      setStarting(false);
    }
  };

  // Keep the typed box synced with speech transcript.
  useEffect(() => {
    if (stt.transcript) setTyped(stt.transcript);
  }, [stt.transcript]);

  const submitAnswer = async () => {
    const answer = (typed || stt.transcript).trim();
    if (!answer || thinking) return;
    if (stt.listening) stt.stop();
    tts.stop();
    setThinking(true);
    setError(null);
    try {
      const data = await studioApi.turn({
        sessionId: studio.sessionId,
        answer,
        presence: camera.getSignals(),
        voice: true,
      });
      const nextQuestion =
        data.next_question ||
        (data.question_text ? { text: data.question_text, audio: data.audio } : null);
      studio.recordTurn({
        answer,
        score: Number(data.score ?? 0),
        feedback: data.feedback,
        model: data.model_answer,
        nextQuestion,
      });
      setTyped("");
      stt.reset();

      // Speak feedback, then the next question (or finish).
      if (data.feedback) tts.speak({ audio: data.feedback_audio, text: data.feedback });

      const isLast =
        data.finished || !nextQuestion || studio.index + 1 >= studio.count;
      if (isLast) {
        await finish();
      } else {
        speakQuestion(nextQuestion);
      }
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally {
      setThinking(false);
    }
  };

  const finish = async () => {
    setThinking(true);
    try {
      const report = await studioApi.finish({
        sessionId: studio.sessionId,
        presence: camera.getSignals(),
      });
      studio.finish(report.report || report);
    } catch (_) {
      studio.finish(null);
    } finally {
      camera.stop();
      tts.stop();
      if (stt.listening) stt.stop();
      setThinking(false);
      setPhase("report");
    }
  };

  const endEarly = () => finish();

  // --- Setup ---
  if (phase === "setup") {
    return (
      <div className="p-4 lg:p-6 max-w-4xl mx-auto space-y-5">
        <div className="rise" style={{ "--d": "0ms" }}>
          <h1 className="text-2xl font-bold text-gray-50">AI Interview Studio</h1>
          <p className="text-sm text-gray-500 mt-1">
            A live, voice + camera interview. The closest thing to the real room.
          </p>
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <SetupWizard onStart={start} starting={starting} />
      </div>
    );
  }

  // --- Report ---
  if (phase === "report") {
    return (
      <div className="p-4 lg:p-6">
        <FinalReport
          report={studio.report}
          turns={studio.turns}
          presence={camera.getSignals()}
          onDone={() => { studio.reset(); setPhase("setup"); }}
        />
      </div>
    );
  }

  // --- Live ---
  const progress = studio.count ? Math.round((studio.index / studio.count) * 100) : 0;
  return (
    <div className="p-4 lg:p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-400">
          {studio.domain} · {studio.level} · Q{Math.min(studio.index + 1, studio.count)}/{studio.count}
        </p>
        <Button size="sm" variant="ghost" onClick={endEarly}>
          <SkipForward size={13} className="inline mr-1" /> End & get report
        </Button>
      </div>
      <div className="h-1 rounded-full bg-gray-800 overflow-hidden">
        <div className="h-full bg-cyan-500 transition-all duration-500" style={{ width: `${progress}%` }} />
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <InterviewerAvatar speaking={tts.speaking} thinking={thinking} />
        <CameraTile
          videoRef={camera.videoRef}
          active={camera.active}
          presencePct={camera.presencePct}
          facePresent={camera.facePresent}
          error={camera.error}
        />
      </div>

      <LiveSubtitles
        question={studio.currentQuestion?.text}
        transcript={typed}
        interim={stt.interim}
        listening={stt.listening}
      />

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="flex items-end gap-2">
        {stt.supported && (
          <button
            onClick={() => (stt.listening ? stt.stop() : stt.start())}
            className={`shrink-0 h-11 w-11 rounded-xl flex items-center justify-center transition ${
              stt.listening ? "bg-red-600 text-white" : "bg-gray-800 text-gray-300 hover:text-white"
            }`}
          >
            {stt.listening ? <MicOff size={18} /> : <Mic size={18} />}
          </button>
        )}
        <textarea
          value={typed}
          onChange={(e) => setTyped(e.target.value)}
          rows={2}
          placeholder="Speak, or type your answer here…"
          className="flex-1 resize-none bg-gray-900 border border-gray-800 rounded-xl px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-cyan-700"
        />
        <Button onClick={submitAnswer} disabled={thinking || !(typed || stt.transcript).trim()}>
          {thinking ? <Spinner size={16} /> : <><Send size={15} className="inline mr-1" />Answer</>}
        </Button>
      </div>
    </div>
  );
}