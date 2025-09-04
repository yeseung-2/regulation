import React, { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from 'remark-gfm';
import { API_BASE_URL } from "../config";

const RequiredDataInput = ({ fields, chunks, tableTexts, tableInputs, setTableInputs, draft, setDraft }) => {
  const [inputs, setInputs] = useState({});
  
  const [improvement, setImprovement] = useState("");
  const topicId = window.location.pathname.split("/").pop();
  const company = "테스트회사";

  const normalize = (str) =>
    str?.replace(/[\s()%\/+.,-]/g, "").toLowerCase(); // 공백, 괄호, 특수문자 제거


  // 문자열 유사도 계산 함수 (Levenshtein 기반)
  const getSimilarity = (str1, str2) => {
    const longer = str1.length > str2.length ? str1 : str2;
    const shorter = str1.length > str2.length ? str2 : str1;

    const longerLength = longer.length;
    if (longerLength === 0) return 1.0;

    const editDistance = (s1, s2) => {
      const costs = Array(s2.length + 1).fill(0);
      for (let i = 0; i <= s1.length; i++) {
        let lastValue = i;
        for (let j = 0; j <= s2.length; j++) {
          if (i === 0) costs[j] = j;
          else if (j > 0) {
            let newValue = costs[j - 1];
            if (s1[i - 1] !== s2[j - 1]) {
              newValue = Math.min(newValue, lastValue, costs[j]) + 1;
            }
            costs[j - 1] = lastValue;
            lastValue = newValue;
          }
        }
        if (i > 0) costs[s2.length] = lastValue;
      }
      return costs[s2.length];
    };

    return (longerLength - editDistance(longer, shorter)) / longerLength;
  };

  
  // ✅ 테이블 HTML 추출 함수 정의 (반드시 추가!)
  const extractFilledTableHTML = () => {
    const tables = document.querySelectorAll("table");

    return Array.from(tables).map((table) => {
      const clone = table.cloneNode(true); // 원본을 훼손하지 않도록 복제

      // 모든 input을 해당 value로 치환
      const inputs = clone.querySelectorAll("input");
      inputs.forEach((input) => {
        const text = input.value;
        const td = input.closest("td");
        if (td) {
          td.textContent = text;  // <td>텍스트</td> 형태로 치환
        }
      });

      return clone.outerHTML;
    });
  };



  const handleInputChange = (fieldName, year, value) => {
    setInputs((prev) => ({
      ...prev,
      [fieldName]: {
        ...(prev[fieldName] || {}),
        [year]: value,
      },
    }));
  };

  // ✅ Cloudinary 업로드 함수 추가 (파일 맨 위에 import 아래에 삽입)
  const uploadToCloudinary = async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("upload_preset", "3rd_project");

    const cloudName = "drzx8tgi4"; // ⬅️ 여기에 본인 Cloudinary cloud name 입력

    const res = await fetch(`https://api.cloudinary.com/v1_1/${cloudName}/image/upload`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    return data.secure_url;
  };


useEffect(() => {
  const fetchDraft = async () => {
    try {
              const res = await fetch(`${API_BASE_URL}/environment/load-draft?topic=${topicId}&company=${company}`);
      const data = await res.json();
      setDraft(data.draft || "");
    } catch (err) {
      console.error("❌ 초안 불러오기 실패:", err);
    }
  };

  const fetchInputs = async () => {
    try {
              const res = await fetch(`${API_BASE_URL}/environment/load-inputs?topic=${topicId}&company=${company}`);
      const data = await res.json();
      const saved = data.inputs || {};

      setInputs(saved.inputs || {});
      setImprovement(saved.improvement || "");
      setTableInputs(saved.table || {});
    } catch (err) {
      console.error("❌ 입력값 불러오기 실패:", err);
    }
  };

  fetchDraft();   // ✅ 먼저 초안 불러오기
  fetchInputs();  // ✅ 그다음 입력값 불러오기
}, []);


  useEffect(() => {
    console.log("📥 입력값 상태:", inputs);
  }, [inputs]);


  const tableFieldNames = Array.from(tableTexts || [])
    .flatMap((html) => {
      const el = document.createElement("div");
      el.innerHTML = html;

      const headerRows = el.querySelectorAll("thead tr");
      let 구분Index = -1;

      headerRows.forEach((row) => {
        const headerCells = Array.from(row.querySelectorAll("th, td"));
        headerCells.forEach((cell, idx) => {
          if (cell.textContent.trim() === "구분" && 구분Index === -1) {
            구분Index = idx;
          }
        });
      });

      if (구분Index === -1) return [];

      const rows = el.querySelectorAll("tbody tr");
      return Array.from(rows)
        .map((row) => {
          const cells = row.querySelectorAll("td, th");
          return cells?.[구분Index]?.textContent?.trim();
        })
        .filter(Boolean);
    })
    .map(normalize)
    .filter((val, idx, arr) => arr.indexOf(val) === idx);



  return (
    <div className="mt-10">
      <h2 className="text-xl font-bold mb-4">📥 항목별 데이터 입력</h2>

      {fields
        .filter((field) => {
          const 항목명 = normalize(field.항목);
          return (
            항목명 &&
            !tableFieldNames.some((tableName) => {
              const similarity = getSimilarity(항목명, normalize(tableName));
              return similarity >= 0.9;
            })
          );
        })
        .map((field, idx) => {
        const 항목명 = field.항목?.trim() || `항목${idx + 1}`;
        const 설명 = field.설명 || "설명 없음";
        const 연도들 = Array.isArray(field.연도) ? field.연도 : [];

        const rawUnit = field.단위?.replace(/[*_`~]/g, "") || "";
        const isYesNoField = rawUnit.includes("예/아니오");

        const 단위들 = isYesNoField
          ? [rawUnit]  // ✅ 예/아니오일 경우 단일 항목 유지
          : rawUnit
              .split(/[,\/]/)
              .map((d) => d.replace(/[()]/g, "").trim())
              .filter(Boolean);

        if (단위들.length === 0) 단위들.push("없음");


        return (
          <div key={idx} className="mb-6 border rounded p-4">
            <h3 className="font-semibold text-md mb-1">📝 {항목명}</h3>
            <p className="text-sm text-gray-600 mb-2">
              단위: {field.단위?.replace(/[*_`~]/g, "") || "없음"} | 연도:{" "}
              {연도들.length > 0 ? 연도들.join(", ") : "없음"}
              <br />
              설명: {설명}
            </p>

            {단위들.map((단위, i) => {
              const cleanUnit = 단위.toLowerCase();
              const 필드키 = 단위 === "없음" ? 항목명 : `${항목명} (${단위})`;
              const isYesNoUnit = cleanUnit.includes("예/아니오");
              

              const isImageField = cleanUnit.includes("이미지");
            

              const 수치형단위키워드 = [
                "건", "건수", "건의",
                "명", "사람", "인원",
                "원", "만원", "억원", "백만원", "천원",
                "점", "개", "개소", "개점",
                "%", "비율", "퍼센트",
                "톤", "kg", "㎏", "g", "리터", "㎥", "m3",
                "시간", "분", "일", "일수", "개월", "연", "년",
                "회", "차수"
              ];

              const 텍스트형단위키워드 = [
                "설명", "예/아니오", "text", "주소", "없음"
              ];

              const isNumericUnit = 수치형단위키워드.some((kw) =>
                cleanUnit.includes(kw)
              );
              const isTextLikeUnit = 텍스트형단위키워드.some((kw) =>
                cleanUnit.includes(kw)
              );

              const isTextField =
                cleanUnit.includes("텍스트") ||
                isTextLikeUnit ||
                cleanUnit === "" ||
                cleanUnit === "없음" ||
                (!isNumericUnit && 연도들.length === 0);

              return (
                <div key={i} className="mb-4">
                  <p className="font-semibold text-sm mb-1">📌 {필드키}</p>

              {isImageField ? (
                <>
                  <input
                    type="file"
                    accept="image/*"
                    className="text-sm"
                    onChange={(e) => {
                      const file = e.target.files[0];
                      const previewUrl = file ? URL.createObjectURL(file) : null;

                      // 기존에는 base64 저장
                      // ✅ Cloudinary 업로드 추가
                      uploadToCloudinary(file).then((uploadedUrl) => {
                        setInputs((prev) => ({
                          ...prev,
                          [필드키]: {
                            fileName: file.name,
                            previewUrl,
                            url: uploadedUrl, // ✅ Cloudinary에서 받은 URL 저장
                          },
                        }));
                      });
                    }}
                  />
                  {inputs?.[필드키]?.previewUrl && (
                    <div className="mt-2">
                      <img
                        src={inputs[필드키].previewUrl}
                        alt="미리보기"
                        className="max-h-48 border rounded"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        ✅ {inputs[필드키].fileName}
                      </p>
                    </div>
                  )}
                </>
                  ) : isYesNoUnit ? (  // ✅ 예/아니오일 경우 단일 텍스트 필드
                    <textarea
                      rows={3}
                      className="w-full border px-2 py-1 rounded text-sm"
                      placeholder={`"${필드키}"에 대한 내용을 입력하세요`}
                      value={inputs?.[필드키]?.text || ""}
                      onChange={(e) =>
                        setInputs((prev) => ({
                          ...prev,
                          [필드키]: { text: e.target.value },
                        }))
                      }
                    />
                  ) : isTextField ? (
                    <textarea
                      rows={3}
                      className="w-full border px-2 py-1 rounded text-sm"
                      placeholder={`"${필드키}"에 대한 내용을 입력하세요`}
                      value={inputs?.[필드키]?.text || ""}
                      onChange={(e) =>
                        setInputs((prev) => ({
                          ...prev,
                          [필드키]: { text: e.target.value },
                        }))
                      }
                    />
                  ) : 연도들.length > 0 ? (
                    <div className="flex gap-2 flex-wrap">
                      {연도들.map((year) => (
                        <input
                          key={year}
                          type="text"
                          inputMode="decimal"
                          pattern="^-?\\d*(\\.\\d*)?$"
                          placeholder={`${year}년`}
                          className="border px-2 py-1 rounded w-28 text-sm"
                          value={inputs?.[필드키]?.[year] || ""}
                          onChange={(e) => {
                            const val = e.target.value;
                            if (/^-?\d*(\.\d*)?$/.test(val) || val === "") {
                              handleInputChange(필드키, year, val);
                            }
                          }}
                        />
                      ))}
                    </div>
                  ) : (
                    <input
                      type="text"
                      inputMode="decimal"
                      pattern="^-?\\d*(\\.\\d*)?$"
                      placeholder="수치를 입력하세요"
                      className="border px-2 py-1 rounded w-40 text-sm"
                      value={inputs?.[필드키]?.value || ""}
                      onChange={(e) => {
                        const val = e.target.value;
                        if (/^-?\d*(\.\d*)?$/.test(val) || val === "") {
                          setInputs((prev) => ({
                            ...prev,
                            [필드키]: { value: val },
                          }));
                        }
                      }}
                    />
                  )}
                </div>
              );
            })}
          </div>
        );
      })}

      <div className="mt-6">
        <h3 className="font-semibold mb-2">개선 노력 및 활동</h3>
        <textarea
          rows={4}
          className="border w-full px-2 py-1 text-sm rounded"
          placeholder="예: 2023년 온실가스 감축을 위해 전사 LED 교체, 폐열 회수 시스템 도입 등을 추진했습니다."
          value={improvement}
          onChange={(e) => setImprovement(e.target.value)}
        />
      </div>

        {/* ✅ 관련 이미지 업로드 - 다중, 제목/설명 입력 */}
        <div className="mt-6">
          <h3 className="font-semibold mb-2">관련 이미지 업로드 (여러 개 가능)</h3>
          <input
            type="file"
            accept="image/*"
            multiple
            className="text-sm"
            onChange={async (e) => {
              const files = Array.from(e.target.files);
              const uploadedImages = await Promise.all(
                files.map(async (file) => {
                  const previewUrl = URL.createObjectURL(file);
                  const uploadedUrl = await uploadToCloudinary(file);
                  return {
                    fileName: file.name,
                    previewUrl,
                    url: uploadedUrl,
                    title: "",
                    description: "",
                  };
                })
              );
              setInputs((prev) => ({
                ...prev,
                ["관련 이미지"]: [
                  ...(Array.isArray(prev["관련 이미지"]) ? prev["관련 이미지"] : []),
                  ...uploadedImages,
                ]
              }));
            }}
          />
        {(Array.isArray(inputs["관련 이미지"]) ? inputs["관련 이미지"] : []).map((img, idx) => (
            <div key={idx} className="mt-4 border rounded p-3 bg-gray-50 relative">
              {/* ❌ 삭제 버튼 추가 */}
              <button
                onClick={() => {
                  const updated = [...inputs["관련 이미지"]];
                  updated.splice(idx, 1); // 인덱스 기준 제거
                  setInputs((prev) => ({
                    ...prev,
                    ["관련 이미지"]: updated,
                  }));
                }}
                className="absolute top-2 right-2 text-gray-400 hover:text-red-600 text-sm"
                aria-label="삭제"
              >
                ❌
              </button>

              <img src={img.url} alt={img.title || "미리보기"} className="max-h-48 mb-2 rounded" />

              <input
                type="text"
                placeholder="이미지 제목"
                value={img.title || ""}
                onChange={(e) => {
                  const newImages = [...inputs["관련 이미지"]];
                  newImages[idx].title = e.target.value;
                  setInputs((prev) => ({
                    ...prev,
                    ["관련 이미지"]: newImages,
                  }));
                }}
                className="text-sm border px-2 py-1 rounded w-full mb-1"
              />

              <textarea
                placeholder="간단한 설명 입력"
                value={img.description || ""}
                onChange={(e) => {
                  const newImages = [...inputs["관련 이미지"]];
                  newImages[idx].description = e.target.value;
                  setInputs((prev) => ({
                    ...prev,
                    ["관련 이미지"]: newImages,
                  }));
                }}
                className="text-sm border px-2 py-1 rounded w-full"
                rows={2}
              />
            </div>
          ))}
      </div>

      <div className="mt-4 flex space-x-2">
        <button
          className="px-4 py-2 bg-gray-700 text-white rounded text-sm hover:bg-gray-800"
          onClick={async () => {
            const payload = {
              topic: topicId,
              company,
              inputs,
              table: tableInputs,
              improvement,
            };

            try {
              await fetch(`${API_BASE_URL}/environment/save-inputs`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
              });
              alert("✅ 입력값이 임시 저장되었습니다.");
            } catch (err) {
              console.error("❌ 입력값 저장 실패:", err);
              alert("❌ 저장 실패");
            }
          }}
        >
          📄 입력값 임시 저장
        </button>


      <button
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
        onClick={async () => {
          // 1) 상태 업데이트가 반영될 시간을 잠깐 기다림
          await new Promise((resolve) => setTimeout(resolve, 100));

          // 2) 입력값이 비었는지 확인
          if (
            Object.keys(inputs).length === 0 &&
            Object.keys(tableInputs).length === 0 &&
            !improvement.trim()
          ) {
            alert("입력값이 없습니다. 데이터를 먼저 입력해주세요.");
            return;
          }

          // 3) 테이블 HTML 추출 및 디버깅 로그
          const filledTableHTMLs = extractFilledTableHTML();
          console.log("✅ 추출된 테이블 수:", filledTableHTMLs.length);
          console.log("📤 전송할 표 HTML들:", extractFilledTableHTML());
            const payload = {
              topic: topicId,
              inputs: {
                ...inputs,
                table: tableInputs,
                filled_table_html: filledTableHTMLs
              },
              chunks,
              table_texts: tableTexts,
              improvement,
            };

          console.log("📤 전송할 전체 payload:", payload);

          // 4) 전송 시도
          try {
              const res = await fetch(`${API_BASE_URL}/environment/generate-draft`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
              });

              if (!res.ok) {
                const text = await res.text();
                console.error("❌ 응답 상태 오류:", res.status, text);
                setDraft(`❌ 서버 응답 오류 (${res.status})`);
                return;
              }

              const data = await res.json();
              setDraft(data.draft);
            } catch (err) {
              console.error("❌ 초안 생성 오류:", err);
              setDraft("❌ 초안 생성 중 오류 발생");
            }
          }}
        >
          📝 초안 생성
        </button>
      </div>
      </div>
);
      };


      export default RequiredDataInput;