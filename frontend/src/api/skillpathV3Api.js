// FILE: frontend/src/api/skillpathV3Api.js
// v12 SkillPath API client. Self-contained — creates its own axios instance so it
// cannot break on a missing shared client file.
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",
});

// attach the student token on every request (same key the rest of the app uses)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("atlas_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const listDomains = () =>
  api.get("/skillpath/domains").then((r) => r.data);

export const getRoadmap = (domainId, planMonths) =>
  api
    .get(`/skillpath/roadmap/${domainId}`, {
      params: planMonths ? { plan_months: planMonths } : {},
    })
    .then((r) => r.data);

export const getLearnCard = (subtopicId) =>
  api.get(`/skillpath/learn/${subtopicId}`).then((r) => r.data);

export const getSubtopicPills = (topicId) =>
  api.get(`/skillpath/subtopics/${topicId}`).then((r) => r.data);

export const getPracticeQuestion = (subtopicId, position) =>
  api
    .get(`/skillpath/practice/${subtopicId}/question`, { params: { position } })
    .then((r) => r.data);

export const submitAttempt = (questionId, studentAnswer) =>
  api
    .post("/skillpath/practice/attempt", {
      question_id: questionId,
      student_answer: studentAnswer,
    })
    .then((r) => r.data);

export const revealAnswer = (questionId) =>
  api
    .post("/skillpath/practice/reveal", { question_id: questionId })
    .then((r) => r.data);

export const getEnrollmentState = (planId) =>
  api
    .get("/enrollment/state", { params: { plan_id: planId } })
    .then((r) => r.data);

export const listEnrollments = () =>
  api.get("/enrollment/list").then((r) => r.data);

export const enrollDomain = (domainId, planId) =>
  api
    .post("/enrollment/enroll", { domain_id: domainId, plan_id: planId })
    .then((r) => r.data);

export default api;