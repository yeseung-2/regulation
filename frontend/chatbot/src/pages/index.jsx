// src/pages/index.jsx
import EnvIndicatorGrid from "./components/EnvIndicatorGrid";

const data = [
  { code: "KBZ-EN00", name: "환경경영 전략" },
  { code: "KBZ-EN11", name: "환경경영 체계" },
  { code: "KBZ-EN12", name: "환경 투자" },
  { code: "KBZ-EN13", name: "환경 컴플라이언스" },
  { code: "KBZ-EN21", name: "원부자재" },
  { code: "KBZ-EN22", name: "온실가스 및 에너지" },
  { code: "KBZ-EN23", name: "폐기물 및 재활용" },
  { code: "KBZ-EN24", name: "수자원" },
  { code: "KBZ-EN25", name: "대기오염물질" },
  { code: "KBZ-EN26", name: "생물다양성" }
];

export default function Home() {
  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold mb-4 flex items-center">
        <span className="mr-2 text-green-500">🍃</span>환경 지표 목록
      </h1>
      <EnvIndicatorGrid items={data} />
    </main>
  );
}
