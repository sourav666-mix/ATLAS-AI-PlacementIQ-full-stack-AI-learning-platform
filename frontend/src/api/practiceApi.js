// practiceApi.js - attempt / reveal
// FILE: frontend/src/api/practiceApi.js
// BATCH 26 / v10 SkillPath (new) - The cost-model pair:
//   attempt(questionId, answer)  -> POST /practice/attempt  (ONE scored AI call)
//   reveal(questionId)           -> /practice/reveal        (pure DB read, NO AI)

import api from "./axios";

const practiceApi = {
  // Backend route: POST /practice/questions/{qid}/attempt with {student_answer}.
  // Falls back to the older flat form for backends that still use it.
  attempt: async (question_id, answer) => {
    try {
      const r = await api.post(`/practice/questions/${question_id}/attempt`, {
        student_answer: answer,
      });
      return r.data;
    } catch (err) {
      if (err?.response?.status === 404 || err?.response?.status === 405) {
        const r = await api.post("/practice/attempt", { question_id, answer });
        return r.data;
      }
      throw err;
    }
  },

  // Backend route: GET /practice/questions/{qid}/reveal (pure DB read).
  reveal: async (question_id) => {
    try {
      const r = await api.get(`/practice/questions/${question_id}/reveal`);
      return r.data;
    } catch (err) {
      if (err?.response?.status === 404 || err?.response?.status === 405) {
        const r = await api.get(`/practice/reveal/${question_id}`);
        return r.data;
      }
      throw err;
    }
  },
};

export default practiceApi;