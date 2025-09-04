import React, { useState, useRef } from "react";
import axios from "axios";
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import Header from "./components/Header";

const templateOptions = [
  "환경경영 지침(안)",
  "환경오염물질관리 규정(안)",
  "온실가스배출관리 규정(안)",
  "대기오염물질관리 규정(안)",
  "폐수배출관리 규정(안)",
  "화학물질관리 규정(안)",
  "인권경영 규정(안)",
  "안전보건관리 지침(안)",
  "공정거래 지침(안)",
  "취업규칙",
  "사회공헌 지침(안)",
  "개인정보보호 규정(안)",
  "윤리경영 지침(안)",
  "ESG 경영 지침(안)"
];

function ESGTemplatesPage() {
  const [selected, setSelected] = useState("");
  const [company, setCompany] = useState("");
  const [rawResult, setRawResult] = useState("");
  const [finalResult, setFinalResult] = useState("");
  const [loading, setLoading] = useState(false);
  const editorRef = useRef();
  const [department, setDepartment] = useState("");
  const [history, setHistory] = useState([
  { date: "", description: "" }]);

  const handleSubmit = async () => {
    if (!selected || !company) return;
    setLoading(true);
    setRawResult("");
    setFinalResult("");

    try {
      const res = await axios.post("http://localhost:8000/template/generate", {
        company,
        topic: selected,
        department,
        history,
      });

      const combined = res.data.template;
      setRawResult(combined);
    } catch (err) {
      console.error(err);
      setRawResult("⚠️ 서버 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const handleApply = () => {
    const edited = editorRef.current.getEditor().root.innerHTML;
    setFinalResult(edited);
  };

  const handleDownloadEditedPDF = async () => {
    if (!finalResult || !company || !selected) return;

    try {
      // ✅ 다운로드 전 '완료 상태'로 저장
      await axios.post("http://localhost:8000/template/save-draft", {
        user_id: "user123",
        company,
        topic: selected,
        html: finalResult,
        department,
        history,
        is_final: true  // 📄 완료 상태 저장
      });

      const res = await fetch("http://localhost:8000/template/download-pdf-from-html", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company,
          topic: selected,
          html: finalResult,
          department,
          history,
        }),
      });

      if (!res.ok) throw new Error("PDF 다운로드 실패");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${company}_${selected}.pdf`;
      a.click();
    } catch (error) {
      alert("PDF 다운로드 중 오류가 발생했습니다.");
      console.error(error);
    }
  };

const handleSaveDraft = async () => {
  if (!finalResult || !selected || !company) {
    alert("회사명, 주제, 내용이 있어야 저장됩니다.");
    return;
  }

  try {
    await axios.post("http://localhost:8000/template/save-draft", {
      user_id: "user123",
      company,
      topic: selected,
      html: finalResult,
      department,
      history,
      is_final: false,  // 💾 임시 저장 상태
    });
    alert("✅ 임시 저장 완료!");
  } catch (error) {
    alert("❌ 임시 저장 중 오류 발생");
    console.error(error);
  }
};

  return (
    <div className="max-w-4xl mx-auto py-12 px-4">
      <Header />
      <br></br>
      <br></br>
      <br></br>
      <h1 className="text-2xl font-bold mb-6">ESG 규정안 작성 도우미</h1>
      <hr></hr>
      <br></br>
      <div className="mb-4">
        <label className="font-semibold mb-2 block">• 규정 주제 선택</label>

        <div className="grid grid-cols-2 gap-2">
          {templateOptions.map((item) => (
            <button
              key={item}
              onClick={() => setSelected(item)}
              className={`border px-3 py-2 rounded-xl text-left hover:bg-green-100 ${
                selected === item ? "bg-green-200" : ""
              }`}
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <hr></hr>
        <br></br>
        <label className="font-semibold mb-2 block">• 기업명 입력</label>
        <input
          type="text"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          className="w-full border px-4 py-2 rounded-xl"
          placeholder="예: 파나시아"
        />
        <div className="mb-4">
        <label className="font-semibold mb-2 block">• 담당 부서 입력</label>
        <input
          type="text"
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
          className="w-full border px-4 py-2 rounded-xl"
          placeholder="예: 지속가능경영팀"
        />
      </div>

      <div className="mb-4">
        <label className="font-semibold mb-2 block">• 제정·개정 이력 입력</label>
        {history.map((item, idx) => (
          <div key={idx} className="flex gap-2 mb-2 items-center">
            <input
              type="text"
              value={item.date}
              onChange={(e) => {
                const updated = [...history];
                updated[idx].date = e.target.value;
                setHistory(updated);
              }}
              placeholder="예: 2022.01.01"
              className="w-1/3 border px-3 py-2 rounded-xl"
            />
            <input
              type="text"
              value={item.description}
              onChange={(e) => {
                const updated = [...history];
                updated[idx].description = e.target.value;
                setHistory(updated);
              }}
              placeholder="예: 최초 제정"
              className="w-2/3 border px-3 py-2 rounded-xl"
            />
            {/* ✅ 삭제 버튼 추가 */}
            <button
              onClick={() => {
                const updated = history.filter((_, i) => i !== idx);
                setHistory(updated);
              }}
              className="text-red-600 text-sm ml-2"
            >
              ✖
            </button>
          </div>
        ))}
        <button
          onClick={() => setHistory([...history, { date: "", description: "" }])}
          className="mt-2 text-sm text-blue-600 underline"
        >
          ➕ 이력 추가
        </button>
      </div>

      </div>

      <button
        onClick={handleSubmit}
        disabled={loading}
        className="bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold px-5 py-2 rounded-xl shadow-md hover:shadow-xl hover:from-green-600 hover:to-emerald-600 active:scale-95 transition-all duration-200"
      >
        {loading ? "작성 중..." : "규정안 생성하기"}
      </button>
          
      {rawResult && (
        <div className="mt-10">
          <h2 className="text-lg font-bold mb-3">✏️ 규정안 수정</h2>
          <ReactQuill
            ref={editorRef}
            value={rawResult}
            onChange={setRawResult}
            style={{ height: "500px" }}
            modules={{
              toolbar: [
                [{ 'header': [1, 2, 3, false] }],
                ['bold', 'italic', 'underline', 'strike'],
                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                [{ 'color': [] }, { 'background': [] }],
                ['link', 'image'],
                ['clean']
              ]
            }}
          />
          <button
            onClick={handleApply}
            className="bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold px-5 py-2 rounded-xl shadow-md hover:shadow-xl hover:from-green-600 hover:to-emerald-600 active:scale-95 transition-all duration-200"
          >
            ✅ 반영하기
          </button>
        </div>
      )}

    {finalResult && (
      <div className="mt-10 border p-6 rounded-xl shadow bg-white">
        <h2 className="text-lg font-bold mb-4">📄 최종 규정안 미리보기</h2>

        {/* ✅ 스타일 태그 추가 */}
        <style>{`
          .preview-html table {
            border-collapse: collapse;
            width: 100%;
            margin-top: 1em;
            font-size: 14px;
          }
          .preview-html th,
          .preview-html td {
            border: 1px solid #ddd;
            padding: 6px 10px;
            vertical-align: top;
            text-align: left;
          }
          .preview-html th {
            background-color: #f9f9f9;
            font-weight: bold;
            text-align: center;
          }
          .preview-html h1,
          .preview-html h2,
          .preview-html h3 {
            font-weight: bold;
            text-align: center;
            margin-top: 1.5em;
          }
          .preview-html p {
            margin-bottom: 0.75em;
          }
        `}</style>

        {/* ✅ HTML 출력 영역 */}
        <div
          id="final-preview"
          className="preview-html text-sm"
          dangerouslySetInnerHTML={{ __html: finalResult }}
        />
        <button
          onClick={handleSaveDraft}
          className="ml-3 bg-yellow-500 text-white px-4 py-2 rounded-xl"
        >
          💾 임시 저장
        </button>
        <button
          onClick={handleDownloadEditedPDF}
          className="mt-4 bg-gray-700 text-white px-5 py-2 rounded-xl hover:bg-gray-800"
        >
          📄규정안 다운로드
        </button>
      </div>
    )}
    </div>
  );
}

export default ESGTemplatesPage;