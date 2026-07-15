// contentApi.js - topic/subtopic/question CRUD + AI regenerate
// FILE: admin-panel/src/api/contentApi.js — BATCH 32 (new)
import api from "./axios";
const contentApi = {
  domains: () => api.get("/admin/content/domains").then(r => r.data),
  topics: (domainId) => api.get("/admin/content/topics", { params: { domain_id: domainId } }).then(r => r.data),
  saveTopic: (topic) => (topic.id ? api.put(`/admin/content/topics/${topic.id}`, topic) : api.post("/admin/content/topics", topic)).then(r => r.data),
  publishTopic: (id) => api.post(`/admin/content/topics/${id}/publish`).then(r => r.data),
  regenerate: (id, kind = "topic") => api.post(`/admin/content/${kind}/${id}/regenerate`).then(r => r.data),
  questions: (subtopicId) => api.get("/admin/content/questions", { params: { subtopic_id: subtopicId } }).then(r => r.data),
  reviewQuestion: (id, action, patch) => api.post(`/admin/content/questions/${id}/${action}`, patch || {}).then(r => r.data),
  arenaQueue: () => api.get("/admin/content/arena-queue").then(r => r.data),
  approveArena: (id, patch) => api.post(`/admin/content/arena-queue/${id}/approve`, patch || {}).then(r => r.data),
};
export default contentApi;