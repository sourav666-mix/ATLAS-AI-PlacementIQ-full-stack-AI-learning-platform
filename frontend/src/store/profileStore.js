// profileStore.js - skill radar + profile bar + daily points
// FILE: frontend/src/store/profileStore.js
// BATCH 25 / v10 Dashboard (new) - skill radar + profile bar + daily points.
// One load() pulls the composed /dashboard payload and NORMALIZES it so the
// UI never guesses shapes: radar always [{skill, score}], profile bar always
// {score, components{}, weights{}, next}, ring always {points, goal}.

import { create } from "zustand";
import progressApi from "../api/progressApi";

const COMPONENT_ORDER = [
  "skill_mastery",
  "assessment_history",
  "coding_strength",
  "interview_readiness",
  "resume_completeness",
  "consistency",
];

const DEFAULT_WEIGHTS = {
  skill_mastery: 25,
  assessment_history: 20,
  coding_strength: 20,
  interview_readiness: 15,
  resume_completeness: 10,
  consistency: 10,
};

function normalizeRadar(raw) {
  if (!raw) return [];
  const list = Array.isArray(raw)
    ? raw
    : Object.entries(raw).map(([skill, score]) => ({ skill, score }));
  return list
    .map((item) => ({
      skill: String(item.skill || item.name || item.axis || "").replace(/_/g, " "),
      score: Math.max(0, Math.min(100, Number(item.score ?? item.value ?? 0))),
    }))
    .filter((item) => item.skill);
}

// The backend sends `what_raises_this_next` as an object {component, message}
// (schemas/dashboard.py NextAction), but the UI renders it as a plain string.
// Pull the message out so we never hand React an object to render.
function normalizeNext(raw) {
  const pick = (v) => {
    if (!v) return null;
    if (typeof v === "string") return v;
    if (typeof v === "object") return v.message || v.text || v.label || null;
    return null;
  };
  return pick(raw.what_raises_this_next) || pick(raw.next) || null;
}

function normalizeWeights(raw) {
  if (!raw) return DEFAULT_WEIGHTS;
  const weights = {};
  COMPONENT_ORDER.forEach((key) => {
    let value = Number(raw[key] ?? DEFAULT_WEIGHTS[key]);
    if (value <= 1) value *= 100; // accept 0.25 or 25
    weights[key] = value;
  });
  return weights;
}

const useProfileStore = create((set) => ({
  loading: false,
  error: null,
  greetingName: null,
  ring: { points: 0, goal: 50 },
  streak: { days: 0, nextMilestone: 7 },
  radar: [],
  profileBar: {
    score: 0,
    components: {},
    weights: DEFAULT_WEIGHTS,
    next: null,
  },
  modules: {},
  nudge: null,
  componentOrder: COMPONENT_ORDER,

  async load() {
    set({ loading: true, error: null });
    try {
      const data = await progressApi.dashboard();
      const ringRaw = data.daily_ring || data.ring || {};
      const streakRaw = data.streak || {};
      const barRaw = data.profile_bar || {};
      const nudgeRaw = data.nudge;
      set({
        ring: {
          points: Number(ringRaw.points_today ?? ringRaw.points ?? 0),
          goal: Number(ringRaw.goal ?? 50) || 50,
        },
        streak: {
          days: Number(streakRaw.days ?? streakRaw.streak ?? 0),
          nextMilestone: Number(
            streakRaw.next_milestone ?? streakRaw.nextMilestone ?? 7
          ),
        },
        radar: normalizeRadar(data.radar),
        profileBar: {
          score: Math.round(Number(barRaw.score ?? 0)),
          components: barRaw.components || {},
          weights: normalizeWeights(barRaw.weights),
          next: normalizeNext(barRaw),
        },
        modules: data.modules || {},
        nudge: nudgeRaw
          ? {
              message:
                nudgeRaw.message || nudgeRaw.text || nudgeRaw.title || null,
              kind: nudgeRaw.type || nudgeRaw.kind || "info",
            }
          : null,
      });
    } catch (err) {
      set({
        error:
          err?.response?.data?.detail ||
          "Couldn't load your dashboard. Check that the backend is running, then refresh.",
      });
    } finally {
      set({ loading: false });
    }
  },
}));

export default useProfileStore;