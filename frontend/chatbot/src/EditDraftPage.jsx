import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { useSearchParams } from "react-router-dom";
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import Header from "./components/Header";
import { useNavigate } from "react-router-dom";

function EditDraftPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();

  const userId = params.get("user_id");
  const topicFromUrl = params.get("topic");

  const [selected, setSelected] = useState("");
  const [company, setCompany] = useState("");
  const [department, setDepartment] = useState("");
  const [history, setHistory] = useState([{ date: "", description: "" }]);
  const [finalResult, setFinalResult] = useState("");
  const editorRef = useRef();

  // ✅ 초안 불러오기
  useEffect(() => {
    if (!userId || !topicFromUrl) return;
    axios
      .get("http://localhost:8000/template/load-draft", {
        params: { user_id: userId, topic: topicFromUrl },
      })
      .then((res) => {
        const data = res.data;
        setSelected(data.topic);
        setCompany(data.company);
        setDepartment(data.department);
        setHistory(data.history);
        setFinalResult(data.html); // 초기 미리보기도 바로 보여줄 수 있음
      })
      .catch((err) => {
        console.error("❌ 초안 불러오기 실패", err);
        alert("초안 불러오기에 실패했습니다.");
      });
  }, [userId, topicFromUrl]);

  const handleApply = () => {
    const edited = editorRef.current.getEditor().root.innerHTML;
    setFinalResult(edited);
  };

  const handleSaveDraft = async () => {
    const html = finalResult;
    try {
      await axios.post("http://localhost:8000/template/save-draft", {
        user_id: userId,
        company,
        topic: selected,
        html,
        department,
        history,
        is_final: false,
      });
      alert("✅ 임시 저장 완료!");
    } catch (error) {
      alert("❌ 임시 저장 중 오류 발생");
      console.error(error);
    }
  };

  const handleDownloadEditedPDF = async () => {
    const html = finalResult;
    try {
      await axios.post("http://localhost:8000/template/save-draft", {
        user_id: userId,
        company,
        topic: selected,
        html,
        department,
        history,
        is_final: true,
      });

      const res = await fetch("http://localhost:8000/template/download-pdf-from-html", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company,
          topic: selected,
          html,
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

  const handleDeleteDraft = async () => {
  const confirmed = window.confirm("정말 이 초안을 삭제하시겠습니까?");
  if (!confirmed) return;

  try {
    await axios.delete("http://localhost:8000/template/delete-draft", {
      params: {
        user_id: userId,
        topic: selected,
      },
    });
    alert("🗑 초안이 삭제되었습니다.");
    navigate("/esg-drafts");  // 목록 페이지로 이동
  } catch (err) {
    alert("❌ 삭제 중 오류 발생");
    console.error(err);
  }
  };

  return (
    <div className="max-w-4xl mx-auto py-12 px-4">
      <Header />
      <br />
      <h1 className="text-2xl font-bold mb-6">✏️ ESG 규정안 수정</h1>
      <hr className="mb-4" />

      <div className="mb-4">
        <label className="font-semibold mb-2 block">• 규정 주제</label>
        <input
          type="text"
          value={selected}
          disabled
          className="w-full border px-4 py-2 rounded-xl bg-gray-100"
        />
      </div>

      <div className="mb-4">
        <label className="font-semibold mb-2 block">• 기업명</label>
        <input
        type="text"
        value={company}
        disabled
        className="w-full border px-4 py-2 rounded-xl bg-gray-100 text-gray-700"
        />
      </div>

      <div className="mb-4">
        <label className="font-semibold mb-2 block">• 담당 부서</label>
        <input
          type="text"
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
          className="w-full border px-4 py-2 rounded-xl"
        />
      </div>

      <div className="mb-4">
        <label className="font-semibold mb-2 block">• 제정·개정 이력</label>
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

      <h2 className="text-lg font-bold mb-3 mt-10">✏️ 규정안 수정</h2>
        {finalResult && (
        <ReactQuill
            key={finalResult}  // ✅ 이게 핵심
            ref={editorRef}
            value={finalResult}
            onChange={setFinalResult}
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
        )}
      <div className="flex gap-3 mt-4">
        <button
          onClick={handleApply}
          className="bg-green-500 text-white px-4 py-2 rounded-xl"
        >
          ✅ 반영하기
        </button>
      </div>

      {finalResult && (
        <div className="mt-10 border p-6 rounded-xl shadow bg-white">
          <h2 className="text-lg font-bold mb-4">📄 최종 규정안 미리보기</h2>

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

          <div
            className="preview-html text-sm"
            dangerouslySetInnerHTML={{ __html: finalResult }}
          />

          <div className="mt-4 flex gap-3">
            <button
              onClick={handleSaveDraft}
              className="bg-yellow-500 text-white px-4 py-2 rounded-xl"
            >
              💾 임시 저장
            </button>
            <button
              onClick={handleDownloadEditedPDF}
              className="bg-gray-800 text-white px-4 py-2 rounded-xl"
            >
              📄 규정안 다운로드
            </button>
            <button onClick={handleDeleteDraft} className="bg-red-700 text-white px-4 py-2 rounded-xl">
                🗑 삭제하기
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default EditDraftPage;
