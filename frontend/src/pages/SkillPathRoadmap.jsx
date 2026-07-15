// SkillPathRoadmap.jsx - [MOD] full roadmap phase/topic view
// FILE: frontend/src/pages/SkillPathRoadmap.jsx
// BATCH 26 / v10 SkillPath (new) - /roadmap. Two states:
//   * No subscription -> the two-step wizard (plan -> domain -> Start),
//     which subscribes then triggers the ONE-TIME roadmap generation.
//   * Subscribed -> the RoadmapTrack rail.
// REPLACES the Placeholder route target from Batch 24.

import React, { useCallback, useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import roadmapApi from "../api/roadmapApi";
import PlanSelection from "../components/SkillPath/PlanSelection";
import DomainSelection from "../components/SkillPath/DomainSelection";
import RoadmapTrack from "../components/SkillPath/RoadmapTrack";
import { Button, Spinner } from "../components/Common";

export default function SkillPathRoadmap() {
  const [state, setState] = useState("loading"); // loading | wizard | track
  const [roadmap, setRoadmap] = useState(null);
  const [plan, setPlan] = useState(null);
  const [domain, setDomain] = useState(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);

  const loadRoadmap = useCallback(async () => {
    try {
      const data = await roadmapApi.myRoadmap();
      // Backend RoadmapOut = { subscription, items }. An existing subscription
      // means "show the track" even if items is empty (RoadmapTrack explains
      // an unseeded domain) — otherwise the user is bounced back into the
      // wizard and re-subscribing 400s ("already have an active subscription").
      const hasTopics =
        (data?.items?.length || data?.phases?.length || data?.topics?.length ||
          (Array.isArray(data) && data.length)) > 0;
      if (hasTopics || data?.subscription) {
        setRoadmap(data);
        setState("track");
      } else {
        setState("wizard");
      }
    } catch (_) {
      setState("wizard"); // 404 = not subscribed yet
    }
  }, []);

  useEffect(() => { loadRoadmap(); }, [loadRoadmap]);

  const start = async () => {
    if (!plan || !domain || starting) return;
    if (!plan.slug || !domain.slug) {
      // Fallback cards (backend not reachable/seeded) carry no slug, and
      // POST /plans/subscribe requires plan_slug + domain_slug.
      setError(
        "Plans haven't loaded from the backend yet — make sure it's running and seeded, then refresh."
      );
      return;
    }
    setStarting(true);
    setError(null);
    try {
      await roadmapApi.subscribe(domain.slug, plan.slug).catch((err) => {
        // Some backends fold subscribe into generate — tolerate a 404 here.
        if (err?.response?.status !== 404) throw err;
      });
      await roadmapApi.generate(domain.slug, plan.slug);
      await loadRoadmap();
    } catch (err) {
      // FastAPI 422s send detail as an array of {loc, msg} — flatten it.
      const detail = err?.response?.data?.detail;
      const msg = Array.isArray(detail)
        ? detail.map((d) => d.msg || JSON.stringify(d)).join("; ")
        : detail || err.message;
      setError(String(msg));
    } finally {
      setStarting(false);
    }
  };

  if (state === "loading") {
    return (
      <div className="h-full flex items-center justify-center">
        <Spinner size={28} />
      </div>
    );
  }

  if (state === "wizard") {
    return (
      <div className="p-4 lg:p-6 max-w-4xl mx-auto space-y-8">
        <div className="rise" style={{ "--d": "0ms" }}>
          <h1 className="text-2xl font-bold text-gray-50">
            Build your SkillPath
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Two choices. Your roadmap generates once and becomes your track to
            placement day.
          </p>
        </div>

        <section className="rise space-y-3" style={{ "--d": "80ms" }}>
          <h2 className="text-sm font-semibold text-gray-300">
            1 · How long do you have?
          </h2>
          <PlanSelection selected={plan} onSelect={setPlan} />
        </section>

        <section className="rise space-y-3" style={{ "--d": "160ms" }}>
          <h2 className="text-sm font-semibold text-gray-300">
            2 · Where are you headed?
          </h2>
          <DomainSelection selected={domain} onSelect={setDomain} />
        </section>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <div className="rise" style={{ "--d": "240ms" }}>
          <Button size="lg" onClick={start} disabled={!plan || !domain || starting}>
            {starting ? (
              <Spinner size={16} />
            ) : (
              <>
                <Sparkles size={16} className="inline mr-2" />
                Generate my roadmap
              </>
            )}
          </Button>
          {plan && domain && !starting && (
            <p className="mt-2 text-xs text-gray-500">
              {domain.name} · {plan.duration_months} months. This runs once —
              your track won't change afterwards, only your mastery will.
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-6 max-w-3xl mx-auto space-y-6">
      <div className="rise" style={{ "--d": "0ms" }}>
        <h1 className="text-2xl font-bold text-gray-50">Your SkillPath</h1>
        <p className="text-sm text-gray-500 mt-1">
          Work top to bottom. Mastery moves only on scored first attempts.
        </p>
      </div>
      <div className="rise" style={{ "--d": "100ms" }}>
        <RoadmapTrack roadmap={roadmap} />
      </div>
    </div>
  );
}