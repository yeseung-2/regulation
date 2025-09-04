import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import RequiredDataInput from "./components/RequiredDataInput";
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import { useRef } from "react";
import { API_BASE_URL } from "./config";

// ✅ 표 입력 컴포넌트
const PageTablesRenderer = ({ page, tableInputs, setTableInputs }) => {
  const [tableHTMLs, setTableHTMLs] = useState([]);

  useEffect(() => {
    const loadTables = async () => {
      try {
        const indexRes = await fetch("/tables_gpt/index.json");
        const indexData = await indexRes.json();
        const files = indexData?.[String(page)] || [];

        const loaded = await Promise.all(
          files.map(async (filename) => {
            const res = await fetch(`/tables_gpt/${filename}`);
            if (!res.ok) return null;
            const html = await res.text();
            return html;
          })
        );

        setTableHTMLs(loaded.filter(Boolean));
      } catch (err) {
        console.error(`❌ page${page} 테이블 로딩 실패:`, err);
      }
    };

    loadTables();
  }, [page]);

  const parseTableToJSX = (html, tableIndex) => {
    const el = document.createElement("div");
    el.innerHTML = html;
    const table = el.querySelector("table");
    const rows = Array.from(table?.querySelectorAll("tr") || []);

    return (
      <table className="table-auto border w-full mb-4 text-sm">
        <tbody>
          {rows.map((tr, rowIdx) => {
            const cells = Array.from(tr.querySelectorAll("th, td"));
            return (
              <tr key={rowIdx}>
                {cells.map((cell, colIdx) => {
                  const isTH = cell.tagName === "TH";
                  const key = `page${page}_table${tableIndex}_r${rowIdx}_c${colIdx}`;
                  return isTH ? (
                    <th key={colIdx} className="border px-2 py-1 bg-gray-100 font-semibold">
                      {cell.textContent}
                    </th>
                  ) : (
                    <td key={colIdx} className="border p-1">
                      <input
                        type="text"
                        className="w-full px-1 py-0.5 text-sm border rounded"
                        value={
                          tableInputs?.[key] !== undefined
                            ? tableInputs[key]
                            : cell.textContent.trim() // HTML 셀 원래 텍스트를 기본값으로 사용
                        }
                        onChange={(e) => {
                          const val = e.target.value;
                          setTableInputs((prev) => ({
                            ...prev,
                            [key]: val,
                          }));
                        }}
                      />
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    );
  };

  return (
    <>
      {tableHTMLs.map((html, idx) => (
        <div key={idx} className="mb-6 border rounded p-3 bg-white shadow">
          {parseTableToJSX(html, idx)}
        </div>
      ))}
    </>
  );
};


// ✅ 메인 페이지
const IndicatorWritePage = () => {
  const { indicator_id: indicatorId } = useParams();
  const [parsedFields, setParsedFields] = useState([]);
  const [chunks, setChunks] = useState([]);
  const [tableTexts, setTableTexts] = useState([]);
  const [summary, setSummary] = useState("");
  const [indicatorMeta, setIndicatorMeta] = useState({ GRI: "", SASB: "", KESG: "" });
  const [loadingFields, setLoadingFields] = useState(false);
  const [tablePages, setTablePages] = useState([]);
  const [draftText, setDraftText] = useState("");

  // ✅ 표 입력값 상태 추가
  const [tableInputs, setTableInputs] = useState({});
  const [draft, setDraft] = useState("");
  const editorRef = useRef();  

  useEffect(() => {
    const extractIndicatorMeta = (chunks) => {
      const fullText = chunks.join("\n");
      let GRI = "", SASB = "", KESG = "";

      const lines = fullText.split("\n");

      const griRaw = fullText.match(/GRI[:\s\-]*([\s\S]*?)SASB/i);
      if (griRaw) {
        GRI = griRaw[1].trim().replace(/[\n\r]/g, " ");
      }

      const kesgMatch = fullText.match(/K-ESG[:\s\-]*([^\n▶]*)/i);
      if (kesgMatch) {
        KESG = kesgMatch[1].trim();
      }

      const sasbParts = [];
      const griIndex = lines.findIndex(line => /GRI/i.test(line));
      for (let i = 0; i < griIndex; i++) {
        const line = lines[i].trim();
        if (
          line.length > 3 &&
          !/^KBZ-[A-Z]{2}\d{2}/.test(line) &&
          /[A-Za-z]/.test(line)
        ) {
          sasbParts.push(line);
        }
      }

      const sasbIndex = lines.findIndex(line => /SASB/i.test(line));
      const kesgIndex = lines.findIndex(line => /K-ESG/i.test(line));
      if (sasbIndex >= 0 && kesgIndex > sasbIndex) {
        for (let i = sasbIndex + 1; i < kesgIndex; i++) {
          const line = lines[i].trim();
          if (line.length > 3) sasbParts.push(line);
        }
      }

      const arrowIndex = lines.findIndex(line => /▶/.test(line));
      if (kesgIndex >= 0) {
        const endIndex = arrowIndex > kesgIndex ? arrowIndex : lines.length;
        for (let i = kesgIndex + 1; i < endIndex; i++) {
          const line = lines[i].trim();
          if (line.length > 3) sasbParts.push(line);
        }
      }

      SASB = sasbParts.join(" ").replace(/\s+/g, " ").trim();

      return { GRI, SASB, KESG };
    };


    const fetchAndInfer = async () => {
      try {
        setLoadingFields(true);

        const fetchRes = await axios.post(`${API_BASE_URL}/environment/fetch-data`, {
          topic: indicatorId,
          company: "테스트회사",
          department: "",
          history: [],
        });

        setChunks(fetchRes.data.chunks || []);
        setTableTexts(fetchRes.data.table_texts || []);
        setTablePages(fetchRes.data.pages || []);

        const meta = extractIndicatorMeta(fetchRes.data.chunks || []);
        setIndicatorMeta(meta);

        const inferRes = await axios.post(`${API_BASE_URL}/environment/infer-required-data`, {
          topic: indicatorId,
          chunks: fetchRes.data.chunks || [],
          table_texts: fetchRes.data.table_texts?.map((html) => {
            const el = document.createElement("div");
            el.innerHTML = html;
            return el.innerText;
          }) || [],
        });

        if (Array.isArray(inferRes.data.required_fields)) {
          setParsedFields(inferRes.data.required_fields);
        }

        const summaryRes = await axios.post(`${API_BASE_URL}/environment/summarize-indicator`, {
          topic: indicatorId,
          chunks: fetchRes.data.chunks || [],
          table_texts: fetchRes.data.table_texts || [],
        });

        setSummary(summaryRes.data.summary);

        const draftRes = await axios.get(`${API_BASE_URL}/environment/load-draft?topic=${indicatorId}&company=테스트회사`);
        setDraft(draftRes.data.draft || "");
      } catch (err) {
        console.error("❌ 데이터 로딩 실패:", err);
      } finally {
        setLoadingFields(false);
      }
    };
        const handleSaveDraft = async () => {
        try {
          const res = await axios.post(
            `${API_BASE_URL}/environment/save-draft/${indicatorId}`,
            {
              company: "테스트회사",   // 실제 로그인된 회사명으로 바꿔주세요
              draft: draftText       // textarea 에서 입력받은 값
            }
          );
          if (res.data.success) {
            alert("✅ 임시 저장 완료!");
          }
        } catch (err) {
          console.error("임시 저장 실패:", err);
          alert("❌ 임시 저장에 실패했습니다.");
        }
      };
    

    fetchAndInfer();
  }, [indicatorId]);

  return (
    <div className="max-w-3xl mx-auto py-12 px-4">
      <h1 className="text-2xl font-bold mb-4">지표 입력 페이지</h1>
      <p className="text-sm text-gray-700 mb-6">
        지표 ID: <strong>{indicatorId}</strong>
      </p>

      {indicatorMeta && !indicatorId.startsWith("KBZ-AP") && (
        <div className="mb-6 text-sm bg-blue-50 border border-blue-200 rounded p-4">
          <p><strong>GRI:</strong> {indicatorMeta.GRI || "-"}</p>
          <p><strong>SASB:</strong> {indicatorMeta.SASB || "-"}</p>
          <p><strong>K-ESG:</strong> {indicatorMeta.KESG || "-"}</p>
        </div>
      )}

      {loadingFields && (
        <div className="text-sm text-gray-500 italic mb-6">
          ⏳ 입력 항목 로딩 중...
        </div>
      )}

      {summary && (
        <div className="text-sm bg-gray-50 p-4 rounded border mb-6">
          <h4 className="font-semibold mb-2">🧾 지표 요약 설명</h4>
          <p>{summary}</p>
        </div>
      )}

      {tablePages.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-2">📊 표 작성</h2>
          {tablePages.map((page) => (
            <PageTablesRenderer
              key={page}
              page={page}
              tableInputs={tableInputs}
              setTableInputs={setTableInputs}
            />
          ))}
        </div>
      )}

      {/* ✅ 입력 필드가 없어도 항상 RequiredDataInput을 렌더링 */}
      <RequiredDataInput
        fields={parsedFields}
        chunks={chunks}
        tableTexts={tableTexts}
        tableInputs={tableInputs}
        setTableInputs={setTableInputs}
        draft={draft} 
        setDraft={setDraft}
      />

      {draft && (
        <div className="mt-10">
          <h2 className="text-lg font-bold mb-3">✏️ 보고서 수정</h2>
          <ReactQuill
            ref={editorRef}
            value={draft}
            onChange={setDraft}
            style={{ height: "800px" }}
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

          <div className="mt-4 flex space-x-2">
            <button
              className="px-4 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700"
              onClick={async () => {
                const html = editorRef.current?.getEditor()?.root.innerHTML;
                setDraft(html);
                try {
                  await fetch(`${API_BASE_URL}/environment/save-draft`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ topic: indicatorId, company: "테스트회사", draft: html }),
                  });
                  alert("✅ 초안이 저장되었습니다.");
                } catch {
                  alert("❌ 임시 저장 실패");
                }
              }}
            >
              📄 초안 임시 저장
            </button>

            <button
              className="px-4 py-2 bg-red-500 text-white rounded text-sm hover:bg-red-600"
              onClick={async () => {
                if (!confirm("임시 저장된 초안을 정말 삭제하시겠습니까?")) return;
                try {
                  await fetch(`${API_BASE_URL}/environment/delete-draft`, {
                    method: "DELETE",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ topic: indicatorId, company: "테스트회사" }),
                  });
                  setDraft("");
                  alert("🗑️ 초안이 삭제되었습니다.");
                } catch {
                  alert("❌ 삭제 실패");
                }
              }}
            >
              🗑️ 초안 삭제
            </button>
          </div>
        </div>
      )}    
      </div>
    );
};

export default IndicatorWritePage;
