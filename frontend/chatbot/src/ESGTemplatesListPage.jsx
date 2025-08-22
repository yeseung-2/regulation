import React, { useEffect, useState } from "react";
import axios from "axios";
import Header from "./components/Header";
function ESGTemplatesListPage() {
  const [drafts, setDrafts] = useState([]);

  useEffect(() => {
    const fetchDrafts = async () => {
      try {
        const res = await axios.get("http://localhost:8000/template/list-drafts", {
          params: { user_id: "user123" },  // 필요 시 로그인 연동
        });
        setDrafts(res.data);
      } catch (err) {
        console.error("❌ 목록 불러오기 실패", err);
      }
    };

    fetchDrafts();
  }, []);

  return (
<div className="max-w-6xl mx-auto py-12 px-4">
  <Header />
  <br></br>
  <br></br>
  <h1 className="text-2xl font-bold mb-6">ESG 규정안 목록</h1>

  <table className="w-full border text-sm text-left">
    <thead className="bg-gray-100 font-semibold">
      <tr>
        <th className="border px-4 py-2">규정 주제</th>
        <th className="border px-4 py-2">담당 부서</th>
        <th className="border px-4 py-2">작성(수정)일</th>
        <th className="border px-4 py-2">상태</th>
      </tr>
    </thead>
    <tbody>
      {drafts.map((item, idx) => (
        <tr key={idx} className="hover:bg-gray-50">
        <td className="border px-4 py-2">
          <div className="flex items-center justify-between">
            <span
              className="text-blue-600 underline cursor-pointer hover:text-blue-800"
              onClick={() => {
                const userId = "user123";
                const encodedTopic = encodeURIComponent(item.topic);
                window.location.href = `/edit-draft?user_id=${userId}&topic=${encodedTopic}`;
              }}
            >
              {item.topic}
            </span>

            <button
              onClick={() => {
                alert("✅ PDF 다운로드는 edit 페이지에서 가능하도록 연결해주세요");
              }}
              className="text-gray-500 hover:text-gray-700 text-sm ml-2"
              title="PDF 다운로드"
            >
              📄다운로드
            </button>
          </div>
        </td>
          <td className="border px-4 py-2">{item.department}</td>
          <td className="border px-4 py-2">
            {new Date(item.timestamp).toLocaleDateString()}
          </td>
          <td className="border px-4 py-2">
            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
              item.is_final
                ? "bg-green-100 text-green-700"
                : "bg-yellow-100 text-yellow-700"
            }`}>
              {item.is_final ? "완료" : "임시 저장"}
            </span>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
  );
}

export default ESGTemplatesListPage;
