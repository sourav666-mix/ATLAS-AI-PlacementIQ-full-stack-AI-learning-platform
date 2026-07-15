// Single source of truth for the admin session. Role gates every screen.
import { create } from "zustand";
import { login as apiLogin } from "../api/adminAuthApi";
import { ADMIN_TOKEN_KEY, errMessage } from "../api/axios";

const ROLE_KEY = "atlas_admin_role";
const NAME_KEY = "atlas_admin_name";

function readInitial() {
  return {
    token: localStorage.getItem(ADMIN_TOKEN_KEY) || null,
    role: localStorage.getItem(ROLE_KEY) || null,
    name: localStorage.getItem(NAME_KEY) || null,
  };
}

export const useAdminAuthStore = create((set, get) => ({
  ...readInitial(),
  loading: false,
  error: null,

  isAuthenticated: () => Boolean(get().token),
  isSuperAdmin: () => get().role === "super_admin",

  async signIn(email, password) {
    set({ loading: true, error: null });
    try {
      const data = await apiLogin(email, password);
      const token = data.access_token;
      const role = data.role || "college_admin";
      const name = data.name || data.email || email;

      localStorage.setItem(ADMIN_TOKEN_KEY, token);
      localStorage.setItem(ROLE_KEY, role);
      localStorage.setItem(NAME_KEY, name);

      set({ token, role, name, loading: false, error: null });
      return true;
    } catch (e) {
      set({ loading: false, error: errMessage(e, "Login failed. Check your credentials.") });
      return false;
    }
  },

  signOut() {
    localStorage.removeItem(ADMIN_TOKEN_KEY);
    localStorage.removeItem(ROLE_KEY);
    localStorage.removeItem(NAME_KEY);
    set({ token: null, role: null, name: null, error: null });
  },
}));