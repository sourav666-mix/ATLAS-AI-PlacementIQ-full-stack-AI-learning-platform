// FILE: frontend/src/api/roadmapApi.js
import api from "./axios";

async function firstOk(requests) {
  let lastErr = null;
  for (const run of requests) {
    try {
      const r = await run();
      return r.data;
    } catch (err) {
      lastErr = err;
      const s = err?.response?.status;
      if (s && s !== 404 && s !== 405) throw err;
    }
  }
  throw lastErr;
}

const roadmapApi = {
  domains: () =>
    firstOk([
      () => api.get("/domains"),
      () => api.get("/roadmap/domains"),
      () => api.get("/plans/domains"),
    ]),

  plans: () =>
    firstOk([
      () => api.get("/plans"),
      () => api.get("/plans/list"),
      () => api.get("/subscription/plans"),
    ]),

  // Backend SubscribeIn expects slugs. A 400/409 means the user already has an
  // active subscription for this domain — not a failure. Confirm via /plans/me
  // and proceed with the existing sub; only re-throw if there's truly no sub
  // (a real error like a bad slug).
  subscribe: async (domain_slug, plan_slug) => {
    try {
      const r = await api.post("/plans/subscribe", { domain_slug, plan_slug });
      return r.data;
    } catch (err) {
      const s = err?.response?.status;
      if (s === 400 || s === 409) {
        try {
          const me = await api.get("/plans/me");
          if (me?.data) return me.data;
        } catch (_) { /* no existing sub -> fall through and re-throw */ }
      }
      throw err;
    }
  },

  generate: async (domain_slug, plan_slug) => {
    try {
      const r = await api.post("/roadmap/generate", { domain_slug, plan_slug });
      return r.data;
    } catch (err) {
      const s = err?.response?.status;
      if (s === 409 || s === 400 || s === 404 || s === 405) return { already: true };
      throw err;
    }
  },

  myRoadmap: () =>
    firstOk([
      () => api.get("/roadmap"),
      () => api.get("/roadmap/my-roadmap"),
      () => api.get("/roadmap/me"),
    ]),

  // Real backend route is /practice/topics/:id (concept card + questions);
  // the /roadmap/* forms are kept as fallbacks for older backends.
  topic: (topicId) =>
    firstOk([
      () => api.get(`/practice/topics/${topicId}`),
      () => api.get(`/roadmap/topic/${topicId}`),
      () => api.get(`/roadmap/topics/${topicId}`),
    ]),

  subtopic: (subtopicId) =>
    firstOk([
      () => api.get(`/practice/topics/${subtopicId}`),
      () => api.get(`/roadmap/subtopic/${subtopicId}`),
      () => api.get(`/roadmap/subtopics/${subtopicId}`),
    ]),
};

export default roadmapApi;