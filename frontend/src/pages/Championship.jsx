// Championship.jsx - [NEW] lobby + proctored exam + results
// FILE: frontend/src/pages/Championship.jsx
// BATCH 30 / v10 Championship (new) - /championship. Orchestrates the three
// phases: lobby -> live exam -> result. CRITICALLY, it sets tutorStore.locked
// while the exam is live so the Global Assistant disappears (fairness), and
// clears it on exit. REPLACES the Placeholder route target from Batch 24.

import React, { useCallback, useEffect, useState } from "react";
import championshipApi from "../api/championshipApi";
import useExamStore from "../store/examStore";
import useTutorStore from "../store/tutorStore";
import Lobby from "../components/Championship/Lobby";
import FullscreenExam from "../components/Championship/FullscreenExam";
import ResultView from "../components/Championship/ResultView";
import { Spinner } from "../components/Common";

export default function Championship() {
  const [phase, setPhase] = useState("loading"); // loading | lobby | exam | result
  const [championships, setChampionships] = useState([]);
  const [entering, setEntering] = useState(false);
  const [error, setError] = useState(null);

  const exam = useExamStore();
  const setTutorLocked = useTutorStore((s) => s.setLocked);

  const loadLobby = useCallback(async () => {
    setPhase("loading");
    try {
      const data = await championshipApi.list();
      const list = Array.isArray(data) ? data : data.championships || [];
      setChampionships(list);
      setPhase("lobby");
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
      setPhase("lobby");
    }
  }, []);

  useEffect(() => { loadLobby(); }, [loadLobby]);

  // Lock/unlock the Global Assistant with the exam lifecycle.
  useEffect(() => {
    setTutorLocked(phase === "exam");
    return () => setTutorLocked(false);
  }, [phase, setTutorLocked]);

  const enter = async (championship) => {
    setEntering(true);
    setError(null);
    try {
      const data = await championshipApi.enter(championship.id);
      const paper =
        data.questions ||
        data.question_paper ||
        data.question_paper_json ||
        [];
      // Server returns its authoritative deadline; fall back to now+duration.
      const durationSecs = Number(data.duration_secs ?? 900);
      const deadlineMs =
        (data.deadline_ms) ||
        (data.deadline ? new Date(data.deadline).getTime() : null) ||
        (data.server_time
          ? new Date(data.server_time).getTime() + durationSecs * 1000
          : Date.now() + durationSecs * 1000);

      exam.begin({
        championshipId: championship.id,
        title: championship.title,
        questions: paper,
        deadlineMs,
      });
      setPhase("exam");
    } catch (err) {
      const status = err?.response?.status;
      if (status === 409) {
        setError("You've already used your one attempt for this championship.");
      } else {
        setError(String(err?.response?.data?.detail || err.message));
      }
    } finally {
      setEntering(false);
    }
  };

  const onExamFinished = () => {
    setTutorLocked(false);
    setPhase("result");
  };

  if (phase === "loading") {
    return (
      <div className="h-full flex items-center justify-center">
        <Spinner size={28} />
      </div>
    );
  }

  if (phase === "exam") {
    return <FullscreenExam onFinished={onExamFinished} />;
  }

  if (phase === "result") {
    return (
      <div className="p-4 lg:p-6">
        <ResultView
          result={exam.result}
          locked={exam.locked}
          onBackToLobby={() => { exam.reset(); loadLobby(); }}
        />
      </div>
    );
  }

  // Lobby
  return (
    <div className="p-4 lg:p-6 max-w-3xl mx-auto space-y-5">
      <div className="rise" style={{ "--d": "0ms" }}>
        <h1 className="text-2xl font-bold text-gray-50">Weekly Championship</h1>
        <p className="text-sm text-gray-500 mt-1">
          A proctored, full-screen sprint. 20 questions, 15 minutes, one attempt.
        </p>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <div className="rise" style={{ "--d": "80ms" }}>
        <Lobby championships={championships} onEnter={enter} entering={entering} />
      </div>
    </div>
  );
}