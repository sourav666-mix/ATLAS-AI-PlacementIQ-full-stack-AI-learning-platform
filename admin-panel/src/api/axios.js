// Isolated admin HTTP client. Uses its OWN token key (atlas_admin_token) and its
// OWN axios instance so a student token can never authenticate against admin routes.
import axios from "axios";

const BASE_URL = import.meta.env.VITE_ADMIN_API_URL || "http://localhost:8000";
export const ADMIN_TOKEN_KEY = "atlas_admin_token";

const adminApi = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 20000,
});

adminApi.interceptors.request.use((config) => {
  const token = localStorage.getItem(ADMIN_TOKEN_KEY);
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

adminApi.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    if (status === 401 || status === 403) {
      localStorage.removeItem(ADMIN_TOKEN_KEY);
      const onLogin = window.location.pathname.startsWith("/login");
      if (!onLogin) window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export function errMessage(error, fallback = "Something went wrong.") {
  return (
    error?.response?.data?.detail ||
    error?.response?.data?.message ||
    error?.message ||
    fallback
  );
}

export default adminApi;