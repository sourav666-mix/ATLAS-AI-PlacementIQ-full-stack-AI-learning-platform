// FILE: frontend/src/api/axios.js
// BATCH 24 / v10 Foundation - the ONE axios instance every api client imports.
// GUEST PREVIEW (new) - on a 401 we redirect to /login ONLY when a token was
// actually present (an expired/invalid session). A guest browsing the public
// dashboard has no token, so a stray 401 is swallowed instead of yanking them
// off the page. You only get sent to /login when a real session goes bad.

import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 60000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("atlas_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    if (status === 401) {
      const hadToken = !!localStorage.getItem("atlas_token");
      localStorage.removeItem("atlas_token");
      localStorage.removeItem("atlas_user");
      if (
        hadToken &&
        typeof window !== "undefined" &&
        !window.location.pathname.startsWith("/login") &&
        !window.location.pathname.startsWith("/register")
      ) {
        // Carry the current page so login can return the user here.
        const next = encodeURIComponent(
          window.location.pathname + window.location.search
        );
        window.location.href = `/login?next=${next}`;
      }
    }
    return Promise.reject(error);
  }
);

export default api;