/**
 * ATLAS AI v12 — Career Target store (Zustand).
 * Holds the working profile form, the last computed scores/gaps, and the
 * cached gap report. Deliberately dumb: all scoring math lives on the server.
 */
import { create } from "zustand";
import careerApi from "../api/careerApi";

export const SKILL_LABELS = ["beginner", "learning", "comfortable", "strong", "expert"];
export const SQL_LEVELS = ["none", "basic", "intermediate", "advanced"];
export const SKILL_CATEGORIES = [
  "language", "library", "database", "cloud", "framework", "tool", "core", "soft", "other",
];

const emptyProfile = () => ({
  full_name: "",
  degree: "B.Tech",
  branch: "",
  specialization: "",
  college: "",
  graduation_year: new Date().getFullYear() + 1,
  cgpa: "",
  target_domain: "data_science",
  leetcode_username: "",
  leetcode_easy: 0,
  leetcode_medium: 0,
  leetcode_hard: 0,
  github_url: "",
  linkedin_url: "",
  sql_level: "basic",
  sql_details: "",
  skills: [],
  projects: [],
  internships: [],
  certifications: [],
  resume_filename: "",
  resume_text: "",
  aptitude_self: "learning",
  communication_self: "learning",
  targets: [], // [{company_slug, priority}]
});

const useCareerStore = create((set, get) => ({
  profile: emptyProfile(),
  companies: [],            // pick-list for the chosen domain
  result: null,            // { profile_score, pillars, targets, ... }
  report: null,            // cached gap report (12-week plan)

  loadingCompanies: false,
  saving: false,
  analyzing: false,
  parsingResume: false,
  error: "",

  // ---- profile mutations -------------------------------------------------
  setField: (key, value) =>
    set((s) => ({ profile: { ...s.profile, [key]: value } })),

  setProfile: (patch) =>
    set((s) => ({ profile: { ...s.profile, ...patch } })),

  reset: () => set({ profile: emptyProfile(), result: null, report: null, error: "" }),

  // skills
  addSkill: (skill) =>
    set((s) => ({ profile: { ...s.profile, skills: [...s.profile.skills, skill] } })),
  updateSkill: (i, patch) =>
    set((s) => {
      const skills = s.profile.skills.slice();
      skills[i] = { ...skills[i], ...patch };
      return { profile: { ...s.profile, skills } };
    }),
  removeSkill: (i) =>
    set((s) => ({
      profile: { ...s.profile, skills: s.profile.skills.filter((_, idx) => idx !== i) },
    })),

  // projects
  addProject: (project) =>
    set((s) => ({ profile: { ...s.profile, projects: [...s.profile.projects, project] } })),
  updateProject: (i, patch) =>
    set((s) => {
      const projects = s.profile.projects.slice();
      projects[i] = { ...projects[i], ...patch };
      return { profile: { ...s.profile, projects } };
    }),
  removeProject: (i) =>
    set((s) => ({
      profile: { ...s.profile, projects: s.profile.projects.filter((_, idx) => idx !== i) },
    })),

  // targets (max 3)
  toggleTarget: (company_slug) =>
    set((s) => {
      const current = s.profile.targets;
      const exists = current.find((t) => t.company_slug === company_slug);
      if (exists) {
        return {
          profile: {
            ...s.profile,
            targets: current
              .filter((t) => t.company_slug !== company_slug)
              .map((t, idx) => ({ ...t, priority: idx + 1 })),
          },
        };
      }
      if (current.length >= 3) return {}; // hard cap
      return {
        profile: {
          ...s.profile,
          targets: [...current, { company_slug, priority: current.length + 1 }],
        },
      };
    }),

  setTargetPriority: (company_slug, priority) =>
    set((s) => ({
      profile: {
        ...s.profile,
        targets: s.profile.targets.map((t) =>
          t.company_slug === company_slug ? { ...t, priority } : t
        ),
      },
    })),

  // ---- async actions -----------------------------------------------------
  loadCompanies: async (domain) => {
    set({ loadingCompanies: true, error: "" });
    try {
      const companies = await careerApi.listCompanies(domain);
      set({ companies, loadingCompanies: false });
    } catch (e) {
      set({
        loadingCompanies: false,
        companies: [],
        error:
          e?.response?.data?.detail ||
          `No companies found for that domain. Ask an admin to seed benchmarks.`,
      });
    }
  },

  parseResume: async (file) => {
    set({ parsingResume: true, error: "" });
    try {
      const data = await careerApi.parseResume(file);
      const links = data.detected_links || {};
      set((s) => ({
        parsingResume: false,
        profile: {
          ...s.profile,
          resume_filename: file.name,
          resume_text: data.resume_text || "",
          github_url: s.profile.github_url || links.github || "",
          linkedin_url: s.profile.linkedin_url || links.linkedin || "",
          leetcode_username:
            s.profile.leetcode_username ||
            (links.leetcode ? links.leetcode.split("/").filter(Boolean).pop() : ""),
        },
      }));
      return data.detected_skills || [];
    } catch (e) {
      set({
        parsingResume: false,
        error: e?.response?.data?.detail || "Could not read that resume file.",
      });
      return [];
    }
  },

  saveProfile: async () => {
    set({ saving: true, error: "" });
    try {
      const p = get().profile;
      const payload = {
        ...p,
        cgpa: p.cgpa === "" ? null : Number(p.cgpa),
        leetcode_easy: Number(p.leetcode_easy) || 0,
        leetcode_medium: Number(p.leetcode_medium) || 0,
        leetcode_hard: Number(p.leetcode_hard) || 0,
      };
      const result = await careerApi.saveProfile(payload);
      set({ saving: false, result });
      return result;
    } catch (e) {
      set({
        saving: false,
        error: e?.response?.data?.detail || "Could not save profile. Check your inputs.",
      });
      throw e;
    }
  },

  analyze: async (force = false) => {
    set({ analyzing: true, error: "" });
    try {
      const report = await careerApi.analyze(force);
      set({ analyzing: false, report });
      return report;
    } catch (e) {
      set({
        analyzing: false,
        error: e?.response?.data?.detail || "Analysis failed. Try again.",
      });
      throw e;
    }
  },

  hydrateFromServer: async () => {
    try {
      const result = await careerApi.getProfile();
      set({ result });
      if (result.has_cached_report) {
        try {
          const report = await careerApi.getReport();
          set({ report });
        } catch {
          /* no cached report yet */
        }
      }
    } catch {
      /* no profile yet — first-time user */
    }
  },
}));

export default useCareerStore;