import React from "react";
import EnvIndicatorCard from "./EnvIndicatorCard";

export default function EnvIndicatorGrid({ items }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {items.map((item) => (
        <EnvIndicatorCard
          key={item.code}
          code={item.code}
          title={item.title ?? item.name}
          status={item.status}
          onClick={item.onClick}  // <-- 여기서도 onClick을 전달
        />
      ))}
    </div>
  );
}
