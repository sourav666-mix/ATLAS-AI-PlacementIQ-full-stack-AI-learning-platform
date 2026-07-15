// FILE: frontend/src/components/Common/index.jsx
// BATCH 24 / v10 Foundation (new) - Shared UI primitives used across every
// module: Button, Card, Spinner, Badge, Modal, ProgressRing. Dark-theme
// Tailwind, no external UI lib. Import as:
//   import { Button, Card, Spinner, Badge, Modal, ProgressRing } from "../Common";

import React from "react";

export { default as ErrorBoundary } from "./ErrorBoundary";

export function Button({
  children, onClick, variant = "primary", size = "md",
  disabled = false, type = "button", className = "", full = false,
}) {
  const variants = {
    primary: "bg-cyan-600 hover:bg-cyan-500 text-white",
    ghost: "bg-gray-800 hover:bg-gray-700 text-gray-200",
    danger: "bg-red-600 hover:bg-red-500 text-white",
    success: "bg-emerald-600 hover:bg-emerald-500 text-white",
    outline:
      "border border-gray-700 hover:border-gray-500 text-gray-200 bg-transparent",
  };
  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`rounded-lg font-medium transition disabled:opacity-40 disabled:cursor-not-allowed ${
        variants[variant] || variants.primary
      } ${sizes[size]} ${full ? "w-full" : ""} ${className}`}
    >
      {children}
    </button>
  );
}

export function Card({ children, className = "", onClick }) {
  return (
    <div
      onClick={onClick}
      className={`bg-gray-900 border border-gray-800 rounded-2xl p-5 ${
        onClick ? "cursor-pointer hover:border-gray-700 transition" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}

export function Spinner({ size = 20, className = "" }) {
  return (
    <span
      className={`inline-block animate-spin rounded-full border-2 border-gray-600 border-t-cyan-400 ${className}`}
      style={{ width: size, height: size }}
    />
  );
}

export function Badge({ children, tone = "gray" }) {
  const tones = {
    gray: "bg-gray-800 text-gray-300",
    cyan: "bg-cyan-950 text-cyan-300",
    green: "bg-emerald-950 text-emerald-300",
    amber: "bg-amber-950 text-amber-300",
    red: "bg-red-950 text-red-300",
    pink: "bg-pink-950 text-pink-300",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
        tones[tone] || tones.gray
      }`}
    >
      {children}
    </span>
  );
}

export function Modal({ open, onClose, title, children, maxWidth = "max-w-lg" }) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div
        className={`bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full ${maxWidth}`}
        onClick={(e) => e.stopPropagation()}
      >
        {title && (
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-100">{title}</h3>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-300 text-xl leading-none"
            >
              ×
            </button>
          </div>
        )}
        {children}
      </div>
    </div>
  );
}

// SVG ring used by the dashboard daily-points ring and elsewhere.
export function ProgressRing({
  value = 0, max = 100, size = 96, stroke = 8,
  color = "#22d3ee", track = "#1f2937", label = null,
}) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.max(0, Math.min(1, max ? value / max : 0));
  const offset = circumference * (1 - pct);
  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          stroke={track} strokeWidth={stroke} fill="none"
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          stroke={color} strokeWidth={stroke} fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="absolute text-center">
        {label ?? (
          <span className="text-lg font-bold text-gray-100">
            {Math.round(pct * 100)}%
          </span>
        )}
      </div>
    </div>
  );
}