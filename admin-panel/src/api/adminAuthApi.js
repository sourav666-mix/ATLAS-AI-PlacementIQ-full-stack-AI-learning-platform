// ---- ASSUMED BACKEND CONTRACT (adjust here if your routes differ) ----
//   POST /admin/login  body: { email, password }
//        -> { access_token, role: "super_admin"|"college_admin", name?, email?, college_id? }
//   GET  /admin/me     -> { role, name, email, college_id }   (optional)
import adminApi from "./axios";

export async function login(email, password) {
  const { data } = await adminApi.post("/admin/login", { email, password });
  return data;
}

export async function fetchMe() {
  const { data } = await adminApi.get("/admin/me");
  return data;
}