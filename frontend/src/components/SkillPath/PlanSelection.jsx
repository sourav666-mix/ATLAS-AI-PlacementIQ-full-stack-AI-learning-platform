// PlanSelection.jsx - 3/6/9-month plan picker
// FILE: frontend/src/components/SkillPath/PlanSelection.jsx
// BATCH 26 / v10 SkillPath (new) - "The subscription is dumb on purpose":
// pick a duration, that's it. Plans load from the backend; if the endpoint
// isn't there yet, the three standard durations render without prices.

import React, { useEffect, useState } from "react";
import { Check } from "lucide-react";
import roadmapApi from "../../api/roadmapApi";

const FALLBACK = [
  { id: "_3", name: "3-Month Sprint", duration_months: 3,
    blurb: "Core topics only — final-semester crunch." },
  { id: "_6", name: "6-Month Builder", duration_months: 6,
    blurb: "Core + intermediate depth. The most popular path." },
  { id: "_12", name: "12-Month Mastery", duration_months: 12,
    blurb: "Everything, including advanced + capstone." },
];

export default function PlanSelection({ selected, onSelect }) {
  const [plans, setPlans] = useState(FALLBACK);

  useEffect(() => {
    roadmapApi
      .plans()
      .then((data) => {
        const list = Array.isArray(data) ? data : data.plans || [];
        if (list.length) {
          setPlans(
            list.map((p) => ({
              id: p.id,
              // slug is what POST /plans/subscribe expects (SubscribeIn.plan_slug)
              slug: p.slug || "",
              name: p.name || p.title || `${p.plan_months}-Month`,
              duration_months: p.plan_months || p.duration_months || p.months,
              price: p.price ?? p.price_inr ?? p.amount ?? null,
              blurb: p.description || "",
            }))
          );
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div className="grid sm:grid-cols-3 gap-3">
      {plans.map((plan) => {
        const active = selected?.id === plan.id;
        return (
          <button
            key={plan.id}
            onClick={() => onSelect(plan)}
            className={`relative text-left rounded-2xl border p-5 transition outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
              active
                ? "border-cyan-600 bg-cyan-950/30"
                : "border-gray-800 bg-gray-900 hover:border-gray-600"
            }`}
          >
            {active && (
              <span className="absolute top-3 right-3 h-5 w-5 rounded-full bg-cyan-500 text-gray-950 flex items-center justify-center">
                <Check size={13} />
              </span>
            )}
            <p className="text-3xl font-bold text-gray-50 tabular-nums">
              {plan.duration_months}
              <span className="text-sm text-gray-500 font-medium"> months</span>
            </p>
            <p className="mt-1 text-sm font-semibold text-gray-200">{plan.name}</p>
            {plan.blurb && (
              <p className="mt-1 text-xs text-gray-500">{plan.blurb}</p>
            )}
            {plan.price != null && (
              <p className="mt-3 text-sm text-cyan-300 font-semibold">
                ₹{plan.price}
              </p>
            )}
          </button>
        );
      })}
    </div>
  );
}