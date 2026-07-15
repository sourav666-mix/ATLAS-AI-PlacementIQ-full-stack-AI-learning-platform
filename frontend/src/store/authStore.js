// authStore.js - user + token
// FILE: frontend/src/store/authStore.js
// BATCH 24 / v10 Foundation (new) - user + token. Persists to localStorage
// under the SAME keys the axios interceptor reads (atlas_token / atlas_user)
// so a refresh keeps you logged in and every request stays authenticated.

import { create } from "zustand";
import authApi from "../api/authApi";

function loadUser() {
  try {
    const raw = localStorage.getItem("atlas_user");
    return raw ? JSON.parse(raw) : null;
  } catch (_) {
    return null;
  }
}

const useAuthStore = create((set, get) => ({
  user: loadUser(),
  token: localStorage.getItem("atlas_token") || null,
  loading: false,
  error: null,

  get isAuthenticated() {
    return !!get().token;
  },

  _persist(token, user) {
    if (token) localStorage.setItem("atlas_token", token);
    if (user) localStorage.setItem("atlas_user", JSON.stringify(user));
    set({ token: token ?? get().token, user: user ?? get().user });
  },

  async login(email, password) {
    set({ loading: true, error: null });
    try {
      const data = await authApi.login(email, password);
      const token =
        data.access_token || data.token || (data.data && data.data.access_token);
      if (!token) throw new Error("No token returned");
      localStorage.setItem("atlas_token", token);
      set({ token });
      const user = await authApi.me().catch(() => null);
      get()._persist(token, user);
      return true;
    } catch (err) {
      set({
        error:
          err?.response?.data?.detail ||
          err.message ||
          "Login failed — check your email and password.",
      });
      return false;
    } finally {
      set({ loading: false });
    }
  },

  async register(payload) {
    set({ loading: true, error: null });
    try {
      await authApi.register(payload);
      return await get().login(payload.email, payload.password);
    } catch (err) {
      set({
        error:
          err?.response?.data?.detail ||
          err.message ||
          "Registration failed.",
      });
      return false;
    } finally {
      set({ loading: false });
    }
  },

  // One-tap Google sign-in: the backend creates the account on first login,
  // so this is both "log in with Google" and "sign up with Google".
  async loginWithGoogle(credential) {
    set({ loading: true, error: null });
    try {
      const data = await authApi.google(credential);
      const token =
        data.access_token || data.token || (data.data && data.data.access_token);
      if (!token) throw new Error("No token returned");
      localStorage.setItem("atlas_token", token);
      set({ token });
      const user = await authApi.me().catch(() => null);
      get()._persist(token, user);
      return true;
    } catch (err) {
      set({
        error:
          err?.response?.data?.detail ||
          err.message ||
          "Google sign-in failed. Please try again.",
      });
      return false;
    } finally {
      set({ loading: false });
    }
  },

  async refreshUser() {
    try {
      const user = await authApi.me();
      get()._persist(null, user);
      return user;
    } catch (_) {
      return null;
    }
  },

  logout() {
    localStorage.removeItem("atlas_token");
    localStorage.removeItem("atlas_user");
    set({ user: null, token: null, error: null });
  },
}));

export default useAuthStore;