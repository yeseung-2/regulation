import React, { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom";
import Header from "./components/Header";
import EnvIndicatorGrid from "./components/EnvIndicatorGrid";


const governanceIndicators = [
  { code: "KBZ-GV00", name: "지배구조 경영전략" },
  { code: "KBZ-GV11", name: "이사회 구조" },
  { code: "KBZ-GV12", name: "이사회 활동 성과" },
  { code: "KBZ-GV13", name: "이사회 성과 평가 및 보상" },
  { code: "KBZ-GV14", name: "지배구조 컴플라이언스" },
  { code: "KBZ-GV21", name: "윤리규정 및 지침" },
  { code: "KBZ-GV22", name: "윤리 모니터링" },
  { code: "KBZ-GV23", name: "윤리 컴플라이언스" },
];


export default function GovernanceIndicatorsPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);

  useEffect(() => {
    async function loadStatuses() {
      const res = await fetch("/environment/indicator-status");
      const statusMap = await res.json();

      const merged = governanceIndicators.map(item => ({
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
      <h1 className="text-2xl font-bold mb-6">지배구조 지표 목록</h1>
      <EnvIndicatorGrid items={items} />
    </div>
  );
}


