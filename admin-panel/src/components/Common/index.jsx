// FILE: admin-panel/src/components/Common/index.jsx — BATCH 32 (new)
// Admin UI primitives (violet accent to visually distinguish from the student app).
import React from "react";

export function Button({ children, onClick, variant = "primary", size = "md", disabled, type = "button", full, className = "" }) {
  const v = {
    primary: "bg-violet-600 hover:bg-violet-500 text-white",
    ghost: "bg-gray-800 hover:bg-gray-700 text-gray-200",
    danger: "bg-red-600 hover:bg-red-500 text-white",
    success: "bg-emerald-600 hover:bg-emerald-500 text-white",
    outline: "border border-gray-700 hover:border-gray-500 text-gray-200",
  };
  const s = { sm: "px-3 py-1.5 text-xs", md: "px-4 py-2 text-sm", lg: "px-6 py-3 text-base" };
  return <button type={type} onClick={onClick} disabled={disabled}
    className={`rounded-lg font-medium transition disabled:opacity-40 disabled:cursor-not-allowed ${v[variant]} ${s[size]} ${full ? "w-full" : ""} ${className}`}>{children}</button>;
}
export function Card({ children, className = "" }) {
  return <div className={`bg-gray-900 border border-gray-800 rounded-2xl p-5 ${className}`}>{children}</div>;
}
export function Spinner({ size = 20 }) {
  return <span className="inline-block animate-spin rounded-full border-2 border-gray-600 border-t-violet-400" style={{ width: size, height: size }} />;
}
export function Badge({ children, tone = "gray" }) {
  const t = { gray: "bg-gray-800 text-gray-300", violet: "bg-violet-950 text-violet-300", green: "bg-emerald-950 text-emerald-300", amber: "bg-amber-950 text-amber-300", red: "bg-red-950 text-red-300" };
  return <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${t[tone] || t.gray}`}>{children}</span>;
}
export function Input({ value, onChange, placeholder, type = "text", label }) {
  return (
    <label className="block">
      {label && <span className="text-xs text-gray-400">{label}</span>}
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
        className="mt-1 w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-violet-700" />
    </label>
  );
}
export function EmptyState({ children }) {
  return <p className="text-sm text-gray-500 py-8 text-center">{children}</p>;
}