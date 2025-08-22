// src/components/ui/badge.jsx
import React from "react";

export function Badge({ className = "", variant, children }) {
  // outline 변형만 예시로 처리
  const base = variant === "outline"
    ? "inline-block border px-2 py-0.5 rounded-full text-xs font-medium"
    : "inline-block px-2 py-0.5 rounded-full text-xs font-medium";
  return <span className={`${base} ${className}`}>{children}</span>;
}
