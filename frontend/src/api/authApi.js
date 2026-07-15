// authApi.js - register / login / me
// FILE: frontend/src/api/authApi.js
// BATCH 24 / v10 Foundation (new) - register / login / me against the
// Session-4 auth router (POST /auth/register, POST /auth/login, GET /auth/me).

import api from "./axios";

const authApi = {
  register: (payload) => api.post("/auth/register", payload).then((r) => r.data),
  login: (email, password) =>
    api.post("/auth/login", { email, password }).then((r) => r.data),
  // credential = the ID token from the Google Identity Services button
  google: (credential) =>
    api.post("/auth/google", { credential }).then((r) => r.data),
  me: () => api.get("/auth/me").then((r) => r.data),
};

export default authApi;