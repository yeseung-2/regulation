import{ useState, useEffect } from "react";
import SurveyModal from "./components/SurveyModal";
import ESGResultCard from "./components/ESGResultCard.jsx";// 설문 결과
import Header from "./components/Header";
import axios from "axios";

export default function MyPage() {
  const [showSurvey, setShowSurvey] = useState(false);
  const [hasSubmittedSurvey, setHasSubmittedSurvey] = useState(false); // 임시 플래그

    useEffect(() => {
    const fetchSurvey = async () => {
        try {
        const token = localStorage.getItem("access_token");
        const res = await axios.get("http://localhost:8000/user/profile", {
            headers: {
            Authorization: `Bearer ${token}`
            }
        });
        if (res.data && res.data.industry_ko) {
            setHasSubmittedSurvey(true);
        }
        } catch (err) {
        console.error("설문 상태 조회 실패:", err);
        }
    };

    fetchSurvey();
    }, []);
  return (
    <div className="max-w-screen-xl mx-auto px-6 py-8">
        <Header />
        <br></br>
        <br></br>
      <h1 className="text-2xl font-bold text-green-800 mb-6">마이페이지</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 왼쪽: 설문 영역 */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 shadow">
          {!hasSubmittedSurvey ? (
            <div className="flex flex-col items-start gap-4">
              <p className="text-gray-700 text-sm">
                ESG 특성을 분석하려면 설문을 먼저 진행해주세요.
              </p>
              <button
                onClick={() => setShowSurvey(true)}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
              >
                내 ESG 특성 알아보기
              </button>
            </div>
          ) : (
            <ESGResultCard />
          )}
        </div>

        {/* 오른쪽: 진행률 영역 */}
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 shadow text-center text-gray-500">
          <p>진행률</p>
          <p className="text-sm mt-2">추후 추가 예정</p>
        </div>
      </div>

      {/* 설문 팝업 */}
      {showSurvey && (
        <SurveyModal
          onClose={() => setShowSurvey(false)}
          onSubmit={() => {
            setHasSubmittedSurvey(true); // 실제로는 서버 응답 확인 후
            setShowSurvey(false);
          }}
        />
      )}
    </div>
  );
}
