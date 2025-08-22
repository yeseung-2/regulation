import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import RequiredDataInput from "./components/RequiredDataInput";

const PageTablesRenderer = ({ page }) => {
  const [tableHTMLs, setTableHTMLs] = useState([]);

  useEffect(() => {
    const loadTables = async () => {
      try {
        const indexRes = await fetch("/sasb_tables/index.json");
        const indexData = await indexRes.json();
        const files = indexData?.[String(page)] || [];

        const loaded = await Promise.all(
          files.map(async (filename) => {
            const res = await fetch(`/sasb_tables/${filename}`);
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

  if (tableHTMLs.length === 0) return null;

  return (
    <>
      {tableHTMLs.map((html, idx) => (
        <div
          key={idx}
          className="border rounded p-3 overflow-auto mb-4"
          dangerouslySetInnerHTML={{
            __html: html.replace(
              /<td>\s*<\/td>/g,
              '<td><input type="text" class="border w-full px-1 py-0.5 text-sm rounded" />'
            ),
          }}
        />
      ))}
    </>
  );
};

const SasbWritePage = () => {
  const { indicator_id: indicatorId } = useParams();
  const [parsedFields, setParsedFields] = useState([]);
  const [chunks, setChunks] = useState([]);
  const [tableTexts, setTableTexts] = useState([]);
  const [summary, setSummary] = useState(""); 
  const [tablePages, setTablePages] = useState([]);
  const [loadingFields, setLoadingFields] = useState(false);

  useEffect(() => {
    const fetchAndInfer = async () => {
      try {
        setLoadingFields(true);

        const fetchRes = await axios.post("http://localhost:8000/sasb/fetch-data", {
          topic: indicatorId,
          company: "테스트회사",
          department: "",
          history: [],
        });

        setChunks(fetchRes.data.chunks || []);
        setTableTexts(fetchRes.data.table_texts || []);
        setTablePages(fetchRes.data.pages || []);

        const inferRes = await axios.post("http://localhost:8000/sasb/infer-required-data", {
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

        const summaryRes = await axios.post("http://localhost:8000/sasb/summarize-indicator", {
          topic: indicatorId,
          chunks: fetchRes.data.chunks || [],
          table_texts: fetchRes.data.table_texts || [],
        });

        setSummary(summaryRes.data.summary);
      } catch (err) {
        console.error("❌ 데이터 로딩 실패:", err);
      } finally {
        setLoadingFields(false);
      }
    };

    fetchAndInfer();
  }, [indicatorId]);

  return (
    <div className="max-w-3xl mx-auto py-12 px-4">
      <h1 className="text-2xl font-bold mb-4">SASB 지표 입력 페이지</h1>
      <p className="text-sm text-gray-700 mb-6">
        지표명: <strong>{indicatorId}</strong>
      </p>

      {loadingFields && (
        <div className="text-sm text-gray-500 italic mb-6">
          ⏳ 입력 항목 로딩 중...
        </div>
      )}

      {parsedFields.length > 0 && (
        <>
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
                <PageTablesRenderer key={page} page={page} />
              ))}
            </div>
          )}

          <RequiredDataInput
            fields={parsedFields}
            chunks={chunks}
            tableTexts={tableTexts}
          />
        </>
      )}
    </div>
  );
};

export default SasbWritePage;