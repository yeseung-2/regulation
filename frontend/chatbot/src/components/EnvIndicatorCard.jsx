import React from "react";

export default function EnvIndicatorCard({ code, title, status = "empty", onClick }) {
  let badgeLabel, badgeColor;

  if (status === "empty") {
    badgeLabel = "작성 필요";
    badgeColor = "bg-red-100 text-red-800";
  } else if (status === "draft" || status === "saved") {
    badgeLabel = "작성 중";
    badgeColor = "bg-yellow-100 text-yellow-800";
  } else if (status === "completed") {
    badgeLabel = "완료";
    badgeColor = "bg-green-100 text-green-800";
  } 
  

  return (
    <div
      onClick={onClick}
      className="border rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow"
    >
      <div className="flex items-center justify-between mb-2 space-x-2">
        <h2 className="font-bold text-lg">{code}</h2>
        <span
          className={`inline-block px-3 py-1 text-xs font-medium rounded-full ${badgeColor}`}
        >
          {badgeLabel}
        </span>
      </div>
      <p className="text-sm text-gray-600 mb-4">{title}</p>
    </div>
  );
}
