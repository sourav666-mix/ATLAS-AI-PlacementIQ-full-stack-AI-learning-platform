import { useEffect, useState, useCallback } from "react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { getOverview } from "../api/analyticsApi";
import { errMessage } from "../api/axios";
import { useAdminAuthStore } from "../store/adminAuthStore";
import { LoadingState, ErrorState, EmptyState } from "../components/common/StateViews";

function Kpi({ label, value, sub }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-slate-900">{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-400">{sub}</div>}
    </div>
  );
}

function fmt(n) {
  if (n === null || n === undefined) return "—";
  return typeof n === "number" ? n.toLocaleString("en-IN") : n;
}

export default function AdminDashboard() {
  const isSuper = useAdminAuthStore((s) => s.isSuperAdmin());
  const [state, setState] = useState({ loading: true, error: null, data: null });

  const load = useCallback(async () => {
    setState({ loading: true, error: null, data: null });
    try {
      const data = await getOverview();
      setState({ loading: false, error: null, data });
    } catch (e) {
      setState({ loading: false, error: errMessage(e, "Couldn't load dashboard."), data: null });
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (state.loading) return <LoadingState label="Loading dashboard…" />;
  if (state.error) return <ErrorState message={state.error} onRetry={load} />;

  const d = state.data || {};
  const series = Array.isArray(d.signups_series) ? d.signups_series : [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <Kpi label="Total students" value={fmt(d.total_students)} sub={`${fmt(d.active_students)} active`} />
        <Kpi label="Colleges" value={fmt(d.active_colleges ?? d.total_colleges)} sub="onboarded" />
        {isSuper && <Kpi label="MRR" value={`₹${fmt(d.mrr)}`} sub={`${fmt(d.paid_users)} paid`} />}
        <Kpi label="DAU" value={fmt(d.dau)} sub={`avg streak ${fmt(d.avg_streak)}`} />
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <div className="text-sm font-medium text-slate-700 mb-4">Signups (recent)</div>
        {series.length === 0 ? (
          <EmptyState title="No signup data yet"
            hint="Once the analytics endpoint returns a signups_series, the trend shows here." />
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={series} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                <defs>
                  <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#0f172a" stopOpacity={0.18} />
                    <stop offset="100%" stopColor="#0f172a" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={36} />
                <Tooltip />
                <Area type="monotone" dataKey="value" stroke="#0f172a" strokeWidth={2} fill="url(#g)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}