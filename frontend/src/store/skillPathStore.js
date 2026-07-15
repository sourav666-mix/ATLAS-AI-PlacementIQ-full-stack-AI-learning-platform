// frontend/src/store/skillPathStore.js
/**
 * ATLAS AI 4.0 - v12 SkillPath Reforged: Zustand store.
 *
 * Drives the locked flow: domains -> plan -> roadmap -> learn ->
 * tabs -> arena question -> analysis -> next question -> mastery.
 *
 * The store also keeps the arena timer (question shown -> submitted) so
 * time_taken_seconds rides along with every analysis - deterministic
 * data the backend can use, never decided by an LLM.
 */

import { create } from "zustand";
import skillPathApi from "../api/skillPathApi";

const errText = (err) =>
  err?.response?.data?.detail || err?.message || "Something went wrong";

export const useSkillPathStore = create((set, get) => ({
  // ------------------------------ state --------------------------------
  domains: [],
  pendingDomainKey: null, // chosen on step 1, committed with the plan
  activeDomainId: null,
  roadmap: null, // {domain_id, domain_key, topics[], overall_pct, plan_months}
  learn: null, // TopicLearnResponse
  tabs: null, // SubtopicTabsResponse
  activeSubtopicId: null,
  question: null, // ArenaQuestion
  exhaustedAndRegenerated: false,
  analysis: null, // AnalysisResult
  progress: null, // SubtopicProgressResponse
  questionShownAt: null,

  loadingDomains: false,
  loadingRoadmap: false,
  loadingLearn: false,
  loadingTabs: false,
  loadingQuestion: false,
  analyzing: false,
  error: null,

  // --------------------------- steps 1-2 --------------------------------
  loadDomains: async () => {
    set({ loadingDomains: true, error: null });
    try {
      const { domains } = await skillPathApi.listDomains();
      set({ domains, loadingDomains: false });
    } catch (err) {
      set({ error: errText(err), loadingDomains: false });
    }
  },

  chooseDomain: (domainKey) => set({ pendingDomainKey: domainKey }),

  /** Commits domain + plan together (plan screen is strictly second). */
  commitPlan: async (planMonths) => {
    const { pendingDomainKey } = get();
    if (!pendingDomainKey) return null;
    set({ error: null });
    try {
      const res = await skillPathApi.select(pendingDomainKey, planMonths);
      set({ activeDomainId: res.domain_id });
      return res;
    } catch (err) {
      set({ error: errText(err) });
      return null;
    }
  },

  // ----------------------------- step 3 ---------------------------------
  loadRoadmap: async (domainId) => {
    set({ loadingRoadmap: true, error: null, activeDomainId: domainId });
    try {
      const roadmap = await skillPathApi.getRoadmap(domainId);
      set({ roadmap, loadingRoadmap: false });
    } catch (err) {
      set({ error: errText(err), loadingRoadmap: false });
    }
  },

  // ----------------------------- step 4 ---------------------------------
  loadLearn: async (topicId) => {
    set({ loadingLearn: true, error: null, learn: null });
    try {
      const learn = await skillPathApi.getTopicLearn(topicId);
      set({ learn, loadingLearn: false });
    } catch (err) {
      set({ error: errText(err), loadingLearn: false });
    }
  },

  // --------------------------- steps 5-6 --------------------------------
  loadTabs: async (topicId, domainId) => {
    set({ loadingTabs: true, error: null });
    try {
      const tabs = await skillPathApi.getSubtopicTabs(topicId, domainId);
      set({ tabs, loadingTabs: false });
      // auto-select the first unmastered tab (or the first tab)
      const first =
        tabs.tabs.find((t) => !t.mastered) || tabs.tabs[0] || null;
      if (first) get().selectSubtopic(first.subtopic_id);
      return tabs;
    } catch (err) {
      set({ error: errText(err), loadingTabs: false });
      return null;
    }
  },

  selectSubtopic: (subtopicId) => {
    set({
      activeSubtopicId: subtopicId,
      question: null,
      analysis: null,
      progress: null,
      exhaustedAndRegenerated: false,
    });
    get().loadNextQuestion();
  },

  // ----------------------------- step 7 ---------------------------------
  loadNextQuestion: async () => {
    const { activeSubtopicId, activeDomainId } = get();
    if (!activeSubtopicId || !activeDomainId) return;
    set({ loadingQuestion: true, analysis: null, error: null });
    try {
      const [nq, progress] = await Promise.all([
        skillPathApi.getNextQuestion(activeSubtopicId, activeDomainId),
        skillPathApi.getSubtopicProgress(activeSubtopicId, activeDomainId),
      ]);
      set({
        question: nq.question,
        exhaustedAndRegenerated: nq.exhausted_and_regenerated,
        progress,
        questionShownAt: Date.now(),
        loadingQuestion: false,
      });
    } catch (err) {
      set({ error: errText(err), loadingQuestion: false });
    }
  },

  // ----------------------------- step 8 ---------------------------------
  submitAnswer: async (answerText, runOutput = null) => {
    const { question, activeDomainId, questionShownAt } = get();
    if (!question || !answerText?.trim()) return null;
    set({ analyzing: true, error: null });
    try {
      const analysis = await skillPathApi.analyze(activeDomainId, {
        questionId: question.question_id,
        answerText,
        runOutput,
        timeTakenSeconds: questionShownAt
          ? Math.min(7200, Math.round((Date.now() - questionShownAt) / 1000))
          : null,
      });
      set({ analyzing: false, analysis });
      // refresh tick state + progress strip after the deterministic update
      const { tabs, activeSubtopicId } = get();
      if (tabs) {
        set({
          tabs: {
            ...tabs,
            tabs: tabs.tabs.map((t) =>
              t.subtopic_id === activeSubtopicId && analysis.subtopic_mastered
                ? { ...t, mastered: true, mastery_pct: 100 }
                : t
            ),
          },
        });
      }
      const progress = await skillPathApi.getSubtopicProgress(
        activeSubtopicId,
        activeDomainId
      );
      set({ progress });
      return analysis;
    } catch (err) {
      set({ error: errText(err), analyzing: false });
      return null;
    }
  },

  clearAnalysisAndAdvance: () => {
    set({ analysis: null });
    get().loadNextQuestion();
  },
}));

export default useSkillPathStore;
