// FILE: frontend/src/store/skillpathV3Store.js
// v3 SkillPath shared state (legacy — DomainSelect.jsx / RoadmapDashboard.jsx /
// DomainSwitcher.jsx). Superseded for the main flow by skillPathStore.js (v12
// Reforged, /skillpath). Depends only on zustand + the API client above.
import { create } from "zustand";
import { listDomains, getRoadmap } from "../api/skillpathV3Api";

export const useSkillpathStore = create((set) => ({
  domains: [],
  roadmap: null,
  loading: false,
  error: null,

  loadDomains: async () => {
    set({ loading: true, error: null });
    try {
      const domains = await listDomains();
      set({ domains: Array.isArray(domains) ? domains : [], loading: false });
    } catch (e) {
      set({
        error: e?.response?.data?.detail || e?.message || "Failed to load domains",
        loading: false,
      });
    }
  },

  loadRoadmap: async (domainId, planMonths) => {
    set({ loading: true, error: null });
    try {
      const roadmap = await getRoadmap(domainId, planMonths);
      set({ roadmap, loading: false });
    } catch (e) {
      set({
        error: e?.response?.data?.detail || e?.message || "Failed to load roadmap",
        loading: false,
      });
    }
  },
}));

export default useSkillpathStore;