import React, { useState, useEffect  } from "react";
import { useNavigate } from "react-router-dom";
import Header from "./components/Header";
import EnvIndicatorGrid from "./components/EnvIndicatorGrid";

export default function EnvironmentIndicatorsPage() {
  const navigate = useNavigate();

  
  const defaultItems = [
    { code: "KBZ-EN00", name: "환경경영 전략" },
    { code: "KBZ-EN11", name: "환경경영 체계" },
    { code: "KBZ-EN12", name: "환경 투자" },
    { code: "KBZ-EN13", name: "환경 컴플라이언스" },
    { code: "KBZ-EN21", name: "원부자재" },
    { code: "KBZ-EN22", name: "온실가스 및 에너지" },
    { code: "KBZ-EN23", name: "폐기물 및 재활용" },
    { code: "KBZ-EN24", name: "수자원" },
    { code: "KBZ-EN25", name: "대기오염물질" },
    { code: "KBZ-EN26", name: "생물다양성" },
  ];

  // 1) items 상태 선언 (초기엔 빈 배열)
  const [items, setItems] = useState([]);

  // 2) 마운트 시점에 DB에서 상태 맵을 가져와 병합
  useEffect(() => {
    console.log("▶ loadStatuses 실행");
    async function loadStatuses() {
      try {
        const res = await fetch("/environment/indicator-status");
        const statusMap = await res.json(); // e.g. { KBZ-EN00: "saved", ... }
        console.log("▶ statusMap:", statusMap);

        const merged = defaultItems.map(item => ({
          ...item,
          status: statusMap[item.code] || "empty"
        }));
        setItems(merged);
      } catch (err) {
        console.error("상태 불러오기 에러", err);
        // 실패 시 모두 empty
        setItems(defaultItems.map(item => ({ ...item, status: "empty" })));
      }
    }
    loadStatuses();
  }, []);

  // 3) 클릭 핸들러
  function handleCardClick(code) {
    // 작성시 draft 상태로
    setItems(prev =>
      prev.map(i => i.code === code ? { ...i, status: i.status === "empty" ? "draft" : i.status } : i)
    );
    navigate(`/write/indicator/${code}`);
  }

  // 4) 임시 저장 핸들러 (API 호출 후)
  async function handleSaveDraft(code, currentDraftText) {
  await axios.post(
   "http://localhost:8000/environment/save-draft",
   {
     topic:   indicatorId,
     company: "테스트회사",
     draft:   draftText
   }
   // axios 기본 헤더가 이미 application/json 이므로 config 생략 가능
 );
  setItems(prev => prev.map(i =>
    i.code === code ? { ...i, status: "saved" } : i
  ));
}

  // 5) 최종 완료 핸들러
  async function handleComplete(code) {
    await fetch(`/environment/complete-indicator/${code}`, { method: "POST" });
    setItems(prev =>
      prev.map(i => i.code === code ? { ...i, status: "completed" } : i)
    );
  }

  if (!items.length) {
    return <div>로딩 중…</div>;
  }

  return (
    <div className="max-w-4xl mx-auto py-12 px-4 pt-24">
      <Header />
      <h1 className="text-2xl font-bold mb-6">🌿 환경 지표 목록</h1>
      <EnvIndicatorGrid
        items={items.map(item => ({
          ...item,
          title: item.name,
          onClick: () => handleCardClick(item.code),
          onSave: () => handleSaveDraft(item.code),
          onComplete: () => handleComplete(item.code),
        }))}
      />
    </div>
  );
}