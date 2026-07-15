// TopicLearning.jsx - [NEW] subtopic checklist + concept + runner
// FILE: frontend/src/pages/TopicLearning.jsx
// BATCH 26 / v10 SkillPath (new) - /learn/:topicId. The study screen:
// subtopic checklist on the left; concept card + attempt-first question
// runner on the right. Selecting a subtopic loads its content + questions.
// REPLACES the Placeholder route target from Batch 24 (route gains :topicId).

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import roadmapApi from "../api/roadmapApi";
import SubtopicChecklist from "../components/SkillPath/SubtopicChecklist";
import ConceptCard from "../components/SkillPath/ConceptCard";
import QuestionRunner from "../components/SkillPath/QuestionRunner";
import { Spinner } from "../components/Common";

function normalizeTopic(raw) {
  const t = raw || {};
  const subtopics = (t.subtopics || t.children || []).map((s) => ({
    id: s.id,
    name: s.name || s.title,
    mastery: Math.round(Number(s.mastery_score ?? s.mastery ?? 0)),
    status: s.status,
  }));
  return {
    id: t.id || t.topic_id,
    name: t.name || t.title || null,
    subtopics,
  };
}

function normalizeSubtopic(raw) {
  const s = raw || {};
  // Backend TopicContentOut sends concept_markdown (a plain string);
  // ConceptCard renders string content via { content }.
  let concept =
    s.concept || s.content_card || s.topic_content || s.concept_card || null;
  if (!concept && s.concept_markdown) concept = { content: s.concept_markdown };
  if (typeof concept === "string") concept = { content: concept };
  return {
    concept,
    questions: s.questions || s.topic_questions || [],
  };
}

export default function TopicLearning() {
  const { topicId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [topic, setTopic] = useState(null);
  const [activeSub, setActiveSub] = useState(null);
  const [subData, setSubData] = useState(null);
  const [subLoading, setSubLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resolving, setResolving] = useState(false);

  // Sidebar links to bare /learn (no topic). Auto-resolve the student's
  // current roadmap topic and jump straight in, instead of dead-ending here.
  useEffect(() => {
    if (topicId) return;
    let cancelled = false;
    setResolving(true);
    roadmapApi
      .myRoadmap()
      .then((data) => {
        if (cancelled) return;
        const items = data?.items || data?.topics || [];
        const chosen = items.find((it) => it.status === "current") || items[0];
        if (chosen) {
          navigate(`/learn/${chosen.topic_id || chosen.id}`, {
            replace: true,
            state: { topicName: chosen.title || chosen.name },
          });
        } else {
          setResolving(false);
        }
      })
      .catch(() => { if (!cancelled) setResolving(false); });
    return () => { cancelled = true; };
  }, [topicId, navigate]);

  useEffect(() => {
    if (!topicId) return;
    setTopic(null);
    setActiveSub(null);
    setSubData(null);
    roadmapApi
      .topic(topicId)
      .then((data) => {
        const normalized = normalizeTopic(data);
        // The practice endpoint doesn't echo the title — use the name the
        // roadmap passed along when navigating here.
        if (!normalized.name)
          normalized.name = location.state?.topicName || "Topic";
        setTopic(normalized);
        if (normalized.subtopics.length) {
          selectSub(normalized.subtopics[0]);
        } else {
          // The topic itself carries the content (no subtopic layer)
          setActiveSub({ id: normalized.id, name: normalized.name });
          setSubData(normalizeSubtopic(data));
        }
      })
      .catch((err) =>
        setError(String(err?.response?.data?.detail || err.message))
      );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topicId]);

  const selectSub = useCallback(async (sub) => {
    setActiveSub(sub);
    setSubData(null);
    setSubLoading(true);
    try {
      const data = await roadmapApi.subtopic(sub.id);
      setSubData(normalizeSubtopic(data));
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally {
      setSubLoading(false);
    }
  }, []);

  const questions = useMemo(() => subData?.questions || [], [subData]);

  if (!topicId) {
    if (resolving) {
      return (
        <div className="h-full flex items-center justify-center">
          <Spinner size={28} />
        </div>
      );
    }
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-gray-100">Topic Learning</h1>
        <p className="text-sm text-gray-500 mt-2">
          You don't have an active roadmap yet. Subscribe to a plan + domain on{" "}
          <button
            onClick={() => navigate("/roadmap")}
            className="text-cyan-400 hover:underline"
          >
            My Roadmap
          </button>{" "}
          to start studying.
        </p>
      </div>
    );
  }

  if (error) {
    return <div className="p-8 text-sm text-red-400">{error}</div>;
  }

  if (!topic) {
    return (
      <div className="h-full flex items-center justify-center">
        <Spinner size={28} />
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-6 max-w-6xl mx-auto space-y-4">
      <div className="rise flex items-center gap-3" style={{ "--d": "0ms" }}>
        <button
          onClick={() => navigate("/roadmap")}
          className="text-gray-500 hover:text-gray-300 transition"
          title="Back to roadmap"
        >
          <ArrowLeft size={18} />
        </button>
        <div>
          <h1 className="text-xl font-bold text-gray-50">{topic.name}</h1>
          {activeSub && topic.subtopics.length > 0 && (
            <p className="text-xs text-gray-500">{activeSub.name}</p>
          )}
        </div>
      </div>

      <div className="grid lg:grid-cols-4 gap-4">
        {topic.subtopics.length > 0 && (
          <aside className="rise lg:col-span-1" style={{ "--d": "80ms" }}>
            <p className="text-[11px] uppercase tracking-[0.14em] text-gray-500 mb-2">
              Subtopics
            </p>
            <SubtopicChecklist
              subtopics={topic.subtopics}
              activeId={activeSub?.id}
              onSelect={selectSub}
            />
          </aside>
        )}

        <div
          className={`rise space-y-4 ${
            topic.subtopics.length ? "lg:col-span-3" : "lg:col-span-4"
          }`}
          style={{ "--d": "140ms" }}
        >
          {subLoading ? (
            <div className="py-16 flex justify-center">
              <Spinner />
            </div>
          ) : (
            <>
              <ConceptCard concept={subData?.concept} />
              <QuestionRunner questions={questions} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}