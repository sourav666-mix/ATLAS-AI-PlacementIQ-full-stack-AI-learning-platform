// AdminNavbar.jsx - admin top nav
import { useNavigate } from "react-router-dom";
import { useAdminAuthStore } from "../../store/adminAuthStore";

export default function AdminNavbar({ title }) {
  const navigate = useNavigate();
  const name = useAdminAuthStore((s) => s.name);
  const signOut = useAdminAuthStore((s) => s.signOut);

  function handleSignOut() {
    signOut();
    navigate("/login", { replace: true });
  }

  return (
    <header className="h-16 shrink-0 border-b border-slate-200 bg-white px-6 flex items-center justify-between">
      <h1 className="text-lg font-semibold text-slate-900">{title}</h1>
      <div className="flex items-center gap-4">
        <span className="text-sm text-slate-600">{name || "Admin"}</span>
        <button
          onClick={handleSignOut}
          className="px-3 py-1.5 rounded-lg text-sm border border-slate-300 text-slate-700 hover:bg-slate-100"
        >
          Sign out
        </button>
      </div>
    </header>
  );
}