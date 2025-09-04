import React, { useEffect, useState } from "react";
// 임시로 빈 배열 사용 (실제 데이터는 나중에 추가)
const sasbIndustries = [];

export default function IndustrySearchInput({ value, onSelect }) {
  const [query, setQuery] = useState("");
  const [filteredOptions, setFilteredOptions] = useState([]);

  useEffect(() => {
    if (query.trim() === "") {
      setFilteredOptions([]);
      return;
    }
    const result = sasbIndustries.filter((item) =>
      item.name_ko.includes(query) ||
      item.name_en.toLowerCase().includes(query.toLowerCase()) ||
      item.code.toLowerCase().includes(query.toLowerCase())
    );
    setFilteredOptions(result);
  }, [query]);

  const handleSelect = (item) => {
    onSelect(item);  // ✅ 전체 업종 객체 전달 (name_ko, code, name_en 포함)
    setQuery(`${item.name_ko} (${item.code} - ${item.name_en})`);
    setFilteredOptions([]);
    };

  return (
    <div className="relative">
      <input
        type="text"
        className="w-full px-3 py-2 border rounded"
        placeholder="업종명을 검색하세요 (예: 자동차)"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      {filteredOptions.length > 0 && (
        <ul className="absolute z-10 w-full border bg-white max-h-60 overflow-y-auto rounded shadow">
          {filteredOptions.map((item) => (
            <li
              key={item.code}
              className="px-4 py-2 hover:bg-green-100 cursor-pointer text-sm"
              onClick={() => handleSelect(item)}
            >
              {item.name_ko} ({item.code} - {item.name_en})
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
