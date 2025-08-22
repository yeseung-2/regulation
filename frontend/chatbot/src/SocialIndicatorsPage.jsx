import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Header from "./components/Header";
import EnvIndicatorGrid from "./components/EnvIndicatorGrid";

const socialIndicators = [
  { code: "KBZ-SC00", name: "사회 경영전략" },
  { code: "KBZ-SC11", name: "안전보건경영 체계" },
  { code: "KBZ-SC12", name: "사업장 안전보건 활동" },
  { code: "KBZ-SC13", name: "산업재해" },
  { code: "KBZ-SC14", name: "위험물 관리" },
  { code: "KBZ-SC15", name: "안전보건 컴플라이언스" },
  { code: "KBZ-SC21", name: "노동관행 및 근로기준" },
  { code: "KBZ-SC22", name: "일과 삶의 균형 지원" },
  { code: "KBZ-SC23", name: "인권 리스크 관리" },
  { code: "KBZ-SC24", name: "노동/인권 고충관리" },
  { code: "KBZ-SC31", name: "구성원 역량 강화" },
  { code: "KBZ-SC32", name: "구성원 현황" },
  { code: "KBZ-SC33", name: "다양성 지표" },
  { code: "KBZ-SC41", name: "협력사 행동규범" },
  { code: "KBZ-SC42", name: "공급망 ESG 관리" },
  { code: "KBZ-SC51", name: "개인정보보호 체계" },
  { code: "KBZ-SC52", name: "개인정보보호 컴플라이언스" },
  { code: "KBZ-SC53", name: "제품 및 서비스 품질 관리" },
  { code: "KBZ-SC54", name: "제품 안전 컴플라이언스" },
  { code: "KBZ-SC61", name: "지역사회 상생협력 활동" },
];


export default function SocialIndicatorsPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);

  useEffect(() => {
    async function loadStatuses() {
      const res = await fetch("/environment/indicator-status");
      const statusMap = await res.json();

      
      const merged = socialIndicators.map(item => ({
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
        <h1 className="text-2xl font-bold mb-6">사회 지표 목록</h1>
        <EnvIndicatorGrid items={items} />
      </div>
    );
  }
  

