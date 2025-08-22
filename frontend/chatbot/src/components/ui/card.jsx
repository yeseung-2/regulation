// src/components/ui/card.jsx
import React from "react";

export function Card({ className = "", style, children }) {
  return (
    <div
      style={style}
      className={`rounded-lg bg-white p-4 ${className}`}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = "" }) {
  return <div className={`mb-2 ${className}`}>{children}</div>;
}

export function CardContent({ children, className = "" }) {
  return <div className={className}>{children}</div>;
}
