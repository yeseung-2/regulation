// src/components/ESGResultCard.jsx
import React, { useEffect, useState } from "react";
import axios from "axios";

export default function ESGResultCard() {
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      const token = localStorage.getItem("access_token");
      try {
        const res = await axios.get("http://localhost:8000/user/profile", {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        setProfile(res.data);
      } catch (err) {
        console.error("설문 결과 불러오기 실패", err);
      }
    };

    fetchProfile();
  }, []);

  if (!profile) {
    return <p className="text-sm text-gray-500">설문 결과를 불러오는 중...</p>;
  }

  return (
    <div>
      <h2 className="text-lg font-semibold text-green-800 mb-2">설문 결과</h2>
      <div className="text-sm text-gray-800 space-y-1">
        <p>▶ 업종: <strong>{profile.industry_ko}</strong> ({profile.industry_code})</p>
        <p>▶ 상시 근로자 수: <strong>{profile.employee_count}</strong></p>

        {/* optional */}
        {profile.esg_experience && (
        <p>▶ 보고서 경험: <strong>{profile.esg_experience}</strong></p>
        )}

        {profile.esg_activities?.length > 0 && (
        <div>
            <p>▶ 활동 중인 ESG 항목:</p>
            <ul className="list-disc ml-6">
            {profile.esg_activities.map((act, i) => <li key={i}>{act}</li>)}
            </ul>
        </div>
        )}

        {profile.emphasis_areas?.length > 0 && (
        <div>
            <p>▶ 강조하고 싶은 내용:</p>
            <ul className="list-disc ml-6">
            {profile.emphasis_areas.map((area, i) => <li key={i}>{area}</li>)}
            </ul>
        </div>
        )}

      </div>
    </div>
  );
}
