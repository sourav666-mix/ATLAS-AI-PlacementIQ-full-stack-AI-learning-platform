// ---- ASSUMED CONTRACT (adjust to your admin/analytics.py) ----
//   GET /admin/analytics/overview
//     -> { total_students, active_students, total_colleges, active_colleges,
//          mrr, paid_users, dau, avg_streak, signups_series?: [{label,value}], plan_mix?: [...] }
//   GET /admin/analytics/revenue    GET /admin/analytics/engagement
// Missing fields render as 0/empty — no crash.
import adminApi from "./axios";

export async function getOverview() {
  const { data } = await adminApi.get("/admin/analytics/overview");
  return data || {};
}
export async function getRevenue() {
  const { data } = await adminApi.get("/admin/analytics/revenue");
  return data || {};
}
export async function getEngagement() {
  const { data } = await adminApi.get("/admin/analytics/engagement");
  return data || {};
}