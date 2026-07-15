// DomainSelection.jsx - 7-domain picker
// FILE: frontend/src/components/SkillPath/DomainSelection.jsx
// BATCH 26 / v10 SkillPath (new) - Pick ONE career domain. Domains come
// from the backend (seeded by seed_content.py); icons map by slug.

import React, { useEffect, useState } from "react";
import {
  BarChart3, Braces, BrainCircuit, Check, Cloud, Database, Shield, Wrench,
} from "lucide-react";
import roadmapApi from "../../api/roadmapApi";
import { Spinner } from "../Common";

const ICONS = {
  "data-science": BarChart3,
  "data-analysis": Database,
  "software-engineer": Braces,
  "ai-ml": BrainCircuit,
  "machine-learning": BrainCircuit,
  cloud: Cloud,
  "cloud-engineer": Cloud,
  cyber: Shield,
  "cyber-security": Shield,
  mlops: Wrench,
};

export default function DomainSelection({ selected, onSelect }) {
  const [domains, setDomains] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    roadmapApi
      .domains()
      .then((data) => {
        const list = Array.isArray(data) ? data : data.domains || [];
        setDomains(
          list.map((d) => ({
            id: d.id,
            name: d.name || d.title,
            slug: d.slug || "",
            description: d.description || "",
          }))
        );
      })
      .catch(() =>
        setError(
          "Couldn't load domains. Seed the backend (seed_content.py), then refresh."
        )
      );
  }, []);

  if (error) return <p className="text-sm text-red-400">{error}</p>;
  if (!domains)
    return (
      <div className="py-8 flex justify-center">
        <Spinner />
      </div>
    );

  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {domains.map((domain) => {
        const Icon = ICONS[domain.slug] || Braces;
        const active = selected?.id === domain.id;
        return (
          <button
            key={domain.id}
            onClick={() => onSelect(domain)}
            className={`relative text-left rounded-2xl border p-4 transition outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
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
            <Icon size={20} className="text-cyan-400" />
            <p className="mt-2 font-semibold text-gray-100">{domain.name}</p>
            {domain.description && (
              <p className="mt-1 text-xs text-gray-500 line-clamp-2">
                {domain.description}
              </p>
            )}
          </button>
        );
      })}
    </div>
  );
}