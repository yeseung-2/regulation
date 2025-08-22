import React, { useState } from "react";
import IndustrySearchInput from "./IndustrySearchInput";
import axios from "axios";

export default function SurveyModal({ onClose, onSubmit }) {
  const [industry, setIndustry] = useState(null);
  const [size, setSize] = useState("");
  const [employeeCount, setEmployeeCount] = useState("");
  const [esgExperience, setEsgExperience] = useState("");
  const [esgActivities, setEsgActivities] = useState([]);
  const [emphasisAreas, setEmphasisAreas] = useState([]);

  const handleCheckboxChange = (value, list, setList) => {
    setList((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
    );
  };

    const handleSubmit = async () => {
    try {
        const token = localStorage.getItem("access_token");
        await axios.post("http://localhost:8000/user/survey", {
        industry_ko: industry.name_ko,
        industry_code: industry.code,
        employee_count: employeeCount,
        esg_experience: esgExperience,
        esg_activities: esgActivities,
        emphasis_areas: emphasisAreas
        }, {
        headers: { Authorization: `Bearer ${token}` }
        });

        // ✅ 설문 제출 성공 후 onSubmit 호출
        onSubmit();
    } catch (err) {
        alert("설문 저장 실패: " + (err.response?.data?.detail || err.message));
    }
    };
    
  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex justify-center items-center z-50">
      <div className="bg-white rounded shadow-lg w-full max-w-2xl p-6 relative overflow-y-auto max-h-[90vh]">
        <button
          onClick={onClose}
          className="absolute top-2 right-2 text-gray-500 hover:text-black text-xl"
        >
          ✕
        </button>

        <h2 className="text-xl font-bold mb-4">설문 - ESG 성향 진단</h2>

        {/* 1. 업종 선택 */}
        <div className="mb-5">
          <label className="block mb-1 font-medium">1. 업종</label>
          <IndustrySearchInput value={industry} onSelect={setIndustry} />
        </div>

        {/* 2. 상시 근로자 수 */}
        <div className="mb-5">
          <label className="block mb-1 font-medium">2. 귀사의 상시 근로자 수는 몇 명입니까?</label>
          <p className="text-xs text-gray-500 mb-2">공시 부담과 지표 수준 조절에 사용됩니다.</p>
          {["1~5명", "6~49명", "50~299명", "300명 이상"].map((opt) => (
            <label key={opt} className="block text-sm">
              <input
                type="radio"
                value={opt}
                checked={employeeCount === opt}
                onChange={() => setEmployeeCount(opt)}
                className="mr-2"
              />
              {opt}
            </label>
          ))}
        </div>

        {/* 3. ESG 보고서 경험 */}
        <div className="mb-5">
          <label className="block mb-1 font-medium">3. ESG 보고서 작성 경험이 있습니까?</label>
          <p className="text-xs text-gray-500 mb-2">보고서 작성 난이도와 설명 수준을 결정합니다.</p>
          {["없음 (이번이 첫 작성)", "간단한 형태로 작성해본 적 있음", "외부 자문을 받아 정식 보고서를 낸 경험 있음"].map((opt) => (
            <label key={opt} className="block text-sm">
              <input
                type="radio"
                value={opt}
                checked={esgExperience === opt}
                onChange={() => setEsgExperience(opt)}
                className="mr-2"
              />
              {opt}
            </label>
          ))}
        </div>

        {/* 4. ESG 관련 활동 (복수 선택) */}
        <div className="mb-5">
          <label className="block mb-1 font-medium">4. 현재 귀사가 진행 중인 ESG 관련 활동은 무엇입니까?</label>
          <p className="text-xs text-gray-500 mb-2">복수 선택 가능합니다.</p>
          {[
            "에너지 절감, 온실가스 감축 노력",
            "근로자 복지 개선",
            "산업안전 및 재해 예방 활동",
            "윤리경영, 내부통제",
            "지역사회 참여, 기부 활동",
            "공급망 관리 / 협력업체 공정거래",
            "특별히 해당되는 활동 없음",
            "기타"
          ].map((opt) => (
            <label key={opt} className="block text-sm">
              <input
                type="checkbox"
                checked={esgActivities.includes(opt)}
                onChange={() => handleCheckboxChange(opt, esgActivities, setEsgActivities)}
                className="mr-2"
              />
              {opt}
            </label>
          ))}
        </div>

        {/* 5. 강조하고 싶은 내용 (복수 선택) */}
        <div className="mb-6">
          <label className="block mb-1 font-medium">5. 보고서에서 강조하고 싶은 내용은 무엇입니까?</label>
          <p className="text-xs text-gray-500 mb-2">복수 선택 가능합니다. 전략 방향 설정에 활용됩니다.</p>
          {[
            "환경 (에너지, 탄소배출 등)",
            "사회 (노동, 지역사회 등)",
            "지배구조 (이사회, 윤리 등)",
            "공급망 책임관리",
            "고객/이해관계자와의 소통",
            "공정거래 및 준법"
          ].map((opt) => (
            <label key={opt} className="block text-sm">
              <input
                type="checkbox"
                checked={emphasisAreas.includes(opt)}
                onChange={() => handleCheckboxChange(opt, emphasisAreas, setEmphasisAreas)}
                className="mr-2"
              />
              {opt}
            </label>
          ))}
        </div>

        <button
          onClick={handleSubmit}
          className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700"
            disabled={
            !industry?.name_ko || !industry?.code ||
            !employeeCount || !esgExperience
            }

        >
          저장하기
        </button>
      </div>
    </div>
  );
}
