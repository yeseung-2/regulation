import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Header from "./components/Header";
import EnvIndicatorGrid from "./components/EnvIndicatorGrid";

const appendixIndicators = [
  { code: "KBZ-AP11", name: "GRI Content Index" },
  { code: "KBZ-AP12", name: "SASB Table" },
  { code: "KBZ-AP20", name: "지속가능경영 이니셔티브" },
  { code: "KBZ-AP30", name: "제3자 검증 성명서" }
];


export default function AppendixIndicatorsPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);

  useEffect(() => {
      async function loadStatuses() {
        const res = await fetch("/environment/indicator-status");
        const statusMap = await res.json();
        
        const merged = appendixIndicators.map(item => ({
        code: item.code,
        title: item.name,
        status: statusMap[item.code] || "empty",
        onClick:    () => navigate(`/write/indicator/${item.code}`),
        onSave:     () => console.log("여기에 임시저장 호출"),
        onComplete: () => console.log("여기에 완료 호출"),
      }));
      setItems(merged);
    }
    loadStatuses();
  }, [navigate]);

  if (!items.length) return <div>로딩 중…</div>;
  
  return (
      <div className="max-w-4xl mx-auto py-12 px-4 pt-24">
        <Header />
        <h1 className="text-2xl font-bold mb-6">부록 목록</h1>
        <EnvIndicatorGrid items={items} />
      </div>
    );
  }


