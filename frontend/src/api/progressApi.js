// progressApi.js - [NEW] daily / streak / summary
// FILE: frontend/src/api/progressApi.js
// BATCH 25 / v10 Dashboard (new) - daily / streak / summary + the composed
// dashboard payload (Batch 17 backend). Fetch is defensive about the exact
// path so it works whether your router exposes /dashboard or /dashboard/summary.

import api from "./axios";

async function firstOk(paths) {
  let lastErr = null;
  for (const path of paths) {
    try {
      const r = await api.get(path);
      return r.data;
    } catch (err) {
      lastErr = err;
      if (err?.response?.status && err.response.status !== 404) throw err;
    }
  }
  throw lastErr;
}

const progressApi = {
  dashboard: () => firstOk(["/dashboard/summary", "/dashboard", "/dashboard/"]),
  daily: () => firstOk(["/progress/daily", "/daily-progress/daily"]),
  streak: () => firstOk(["/progress/streak", "/daily-progress/streak"]),
  summary: () => firstOk(["/progress/summary", "/daily-progress/summary"]),
};

export default progressApi;