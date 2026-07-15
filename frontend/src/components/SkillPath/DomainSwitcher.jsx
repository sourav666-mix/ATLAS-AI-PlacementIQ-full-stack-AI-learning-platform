// frontend/src/components/SkillPath/DomainSwitcher.jsx   [NEW v12]
// Add/switch enrolled domains, gated by the plan-tier cap (1 / 2 / 3). The button DISABLES at the cap —
// but the real enforcement is server-side (uq_user_domain + enrollment_service). This is just the surface.
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSkillpathStore } from "../../store/skillpathV3Store";

export default function DomainSwitcher({ planId }) {
  const navigate = useNavigate();
  const { domains, enrollmentState, loadDomains, loadEnrollmentState, addDomain } =
    useSkillpathStore();
  const [open, setOpen] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (!domains.length) loadDomains();
    if (planId) loadEnrollmentState(planId).catch(() => {});
  }, [planId, domains.length, loadDomains, loadEnrollmentState]);

  const cap = enrollmentState?.domain_cap ?? 1;
  const used = enrollmentState?.slots_used ?? 0;
  const canAdd = enrollmentState?.can_add_more ?? false;

  const onAdd = async (domainId) => {
    setErr(null);
    try {
      await addDomain(domainId, planId);
      setOpen(false);
      navigate(`/roadmap/${domainId}`);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Could not add domain");
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-sm hover:border-violet-500/60"
      >
        Domains {used}/{cap} ▾
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-72 rounded-2xl border border-zinc-800 bg-zinc-900 p-2 z-30 shadow-xl">
          <p className="px-2 py-1 text-xs text-zinc-500">
            {canAdd ? `You can add ${cap - used} more domain(s).` : "Cap reached — upgrade your plan to add more."}
          </p>
          {err && <p className="px-2 py-1 text-xs text-rose-400">{err}</p>}
          <div className="max-h-64 overflow-y-auto">
            {domains.map((d) => (
              <button
                key={d.id}
                disabled={!canAdd}
                onClick={() => onAdd(d.id)}
                className="w-full text-left rounded-lg px-2 py-2 text-sm text-zinc-200 hover:bg-zinc-800 disabled:opacity-40"
              >
                {d.name}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}