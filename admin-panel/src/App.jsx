// If your main.jsx ALREADY wraps <App /> in <BrowserRouter>, delete the
// <BrowserRouter> here (you can't nest two).
import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation } from "react-router-dom";
import { useAdminAuthStore } from "./store/adminAuthStore";
import AdminSidebar from "./components/Layout/AdminSidebar";
import AdminNavbar from "./components/Layout/AdminNavbar";
import AdminLogin from "./pages/AdminLogin";
import AdminDashboard from "./pages/AdminDashboard";

const TITLES = {
  "/dashboard": "Dashboard", "/students": "Students", "/content": "Content Management",
  "/colleges": "Colleges", "/revenue": "Revenue & Analytics", "/jobs": "Jobs Board",
  "/championships": "Championships", "/providers": "AI Providers",
};

function RequireAuth() {
  const isAuthed = useAdminAuthStore((s) => s.isAuthenticated());
  const location = useLocation();
  if (!isAuthed) return <Navigate to="/login" replace state={{ from: location }} />;
  return <Outlet />;
}

function RequireSuper() {
  const isSuper = useAdminAuthStore((s) => s.isSuperAdmin());
  if (!isSuper) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}

function Shell() {
  const { pathname } = useLocation();
  const title = TITLES[pathname] || "Admin";
  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      <AdminSidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <AdminNavbar title={title} />
        <main className="flex-1 p-6 overflow-y-auto"><Outlet /></main>
      </div>
    </div>
  );
}

function ComingSoon({ name }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-10 text-center">
      <div className="text-slate-800 font-medium">{name}</div>
      <div className="mt-1 text-sm text-slate-500">This screen ships in an upcoming batch.</div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AdminLogin />} />
        <Route element={<RequireAuth />}>
          <Route element={<Shell />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<AdminDashboard />} />
            <Route path="/students" element={<ComingSoon name="Student Management" />} />
            <Route path="/colleges" element={<ComingSoon name="College Management" />} />
            <Route path="/jobs" element={<ComingSoon name="Jobs Management" />} />
            <Route path="/championships" element={<ComingSoon name="Championship Management" />} />
            <Route element={<RequireSuper />}>
              <Route path="/content" element={<ComingSoon name="Content Management" />} />
              <Route path="/revenue" element={<ComingSoon name="Revenue & Analytics" />} />
              <Route path="/providers" element={<ComingSoon name="AI Providers" />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}