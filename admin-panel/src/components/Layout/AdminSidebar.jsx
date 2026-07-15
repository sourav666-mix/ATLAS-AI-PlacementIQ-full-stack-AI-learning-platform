// AdminSidebar.jsx - admin side nav (role-aware)
// Role-aware navigation. Icons are inline SVG — zero extra dependencies.
import { NavLink } from "react-router-dom";
import { useAdminAuthStore } from "../../store/adminAuthStore";

function Icon({ d }) {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  );
}

const ICONS = {
  dashboard: "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z",
  students: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75",
  content: "M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 4.5A2.5 2.5 0 0 1 6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15z",
  colleges: "M3 21h18M5 21V7l7-4 7 4v14M9 21v-4h6v4",
  revenue: "M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6",
  jobs: "M20 7h-4V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2H4a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1V8a1 1 0 0 0-1-1zM8 7V5h8v2",
  championship: "M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4zM7 4H4v2a3 3 0 0 0 3 3M17 4h3v2a3 3 0 0 1-3 3",
  providers: "M22 12h-4l-3 9L9 3l-3 9H2",
};

const NAV = [
  ["/dashboard", "Dashboard", "dashboard", false],
  ["/students", "Students", "students", false],
  ["/content", "Content", "content", true],
  ["/colleges", "Colleges", "colleges", false],
  ["/revenue", "Revenue", "revenue", true],
  ["/jobs", "Jobs", "jobs", false],
  ["/championships", "Championships", "championship", false],
  ["/providers", "AI Providers", "providers", true],
];

export default function AdminSidebar() {
  const isSuper = useAdminAuthStore((s) => s.isSuperAdmin());
  const items = NAV.filter(([, , , superOnly]) => !superOnly || isSuper);

  return (
    <aside className="w-60 shrink-0 h-screen sticky top-0 border-r border-slate-200 bg-white flex flex-col">
      <div className="px-5 h-16 flex items-center border-b border-slate-200">
        <span className="font-semibold text-slate-900">ATLAS AI</span>
        <span className="ml-2 text-[11px] uppercase tracking-wide text-slate-400">Admin</span>
      </div>
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {items.map(([path, label, iconKey]) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`
            }
          >
            <Icon d={ICONS[iconKey]} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 text-[11px] text-slate-400 border-t border-slate-200">
        {isSuper ? "Super Admin" : "College Admin"}
      </div>
    </aside>
  );
}