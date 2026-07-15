// frontend/src/api/skillPathApi.js
/**
 * ATLAS AI 4.0 - v12 SkillPath Reforged: API client.
 * 1:1 with routers/skillpath_v12.py. Shared axios instance = shared JWT.
 */

import api from "./axios";

export const skillPathApi = {
  /** Step 1 - the nine locked domain cards. Type A. */
  listDomains: () => api.get("/skillpath/domains").then((r) => r.data),

  /** Step 2 - domain FIRST, then plan (3/6/9). Type A. */
  select: (domainKey, planMonths) =>
    api
      .post("/skillpath/select", {
        domain_key: domainKey,
        plan_months: planMonths,
      })
      .then((r) => r.data),

  /** Step 3 - roadmap cards with rings + status. Type A. */
  getRoadmap: (domainId) =>
    api.get(`/skillpath/roadmap/${domainId}`).then((r) => r.data),

  /** Step 4 - LEARN: what/when/how + 5 examples per subtopic. Type A. */
  getTopicLearn: (topicId) =>
    api.get(`/skillpath/topic/${topicId}/learn`).then((r) => r.data),

  /** Steps 5-6 - subtopic tabs with mastery ticks. Type A. */
  getSubtopicTabs: (topicId, domainId) =>
    api
      .get(`/skillpath/topic/${topicId}/subtopics`, {
        params: { domain_id: domainId },
      })
      .then((r) => r.data),

  /** Step 7 - next unseen question, difficulty order. Type A from bank. */
  getNextQuestion: (subtopicId, domainId) =>
    api
      .get(`/skillpath/subtopic/${subtopicId}/next-question`, {
        params: { domain_id: domainId },
      })
      .then((r) => r.data),

  /** Progress strip. Type A. */
  getSubtopicProgress: (subtopicId, domainId) =>
    api
      .get(`/skillpath/subtopic/${subtopicId}/progress`, {
        params: { domain_id: domainId },
      })
      .then((r) => r.data),

  /** Step 8 - THE Type B call: exactly one AI analysis per submission. */
  analyze: (domainId, { questionId, answerText, runOutput, timeTakenSeconds }) =>
    api
      .post(
        "/skillpath/subtopic/analyze",
        {
          question_id: questionId,
          answer_text: answerText,
          run_output: runOutput ?? null,
          time_taken_seconds: timeTakenSeconds ?? null,
        },
        { params: { domain_id: domainId } }
      )
      .then((r) => r.data),
};

export default skillPathApi;