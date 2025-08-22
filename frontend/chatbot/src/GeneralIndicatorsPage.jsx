import React, { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom";
import Header from "./components/Header";
import EnvIndicatorGrid from "./components/EnvIndicatorGrid";

const generalIndicators = [
  { code: "KBZ-SR10", name: "이 보고서에 대하여" },
  { code: "KBZ-SR21", name: "CEO 메시지" },
  { code: "KBZ-SR22", name: "회사 개요" },
  { code: "KBZ-SR23", name: "경제적 가치 창출 및 분배" },
  { code: "KBZ-SR24", name: "ESG 경영 비전 및 성과" },
  { code: "KBZ-SR30", name: "이해관계자 소통 및 중요성 평가" },
];

export default function GeneralIndicatorsPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);

  useEffect(() => {
      async function loadStatuses() {
        const res = await fetch("/environment/indicator-status");
        const statusMap = await res.json();
  
        const merged = generalIndicators.map(item => ({
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
        <h1 className="text-2xl font-bold mb-6">지속가능성 보고 일반</h1>
        <EnvIndicatorGrid items={items} />
      </div>
    );
  }
