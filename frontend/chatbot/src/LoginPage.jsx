import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    try {
    const res = await axios.post("http://localhost:8000/auth/login", {
        email,
        password,
    });

    console.log("✅ 로그인 응답:", res.data);  // ← 추가
    localStorage.setItem("access_token", res.data.access_token);
    navigate("/");
    } catch (err) {
    console.error("❌ 로그인 실패:", err.response?.data || err.message);
    setError("이메일 또는 비밀번호가 올바르지 않습니다.");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
      <div className="bg-white p-8 rounded shadow-md w-80">
        <h2 className="text-2xl font-bold mb-4 text-center">로그인</h2>
        <form onSubmit={handleLogin}>
          <input
            type="email"
            placeholder="이메일"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 border rounded mb-3"
            required
          />
          <input
            type="password"
            placeholder="비밀번호"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border rounded mb-4"
            required
          />
          {error && <p className="text-red-500 text-sm mb-3">{error}</p>}
          <button
            type="submit"
            className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700"
          >
            로그인
          </button>
          <div className="mt-4 text-center">
            <span className="text-sm text-gray-600">계정이 없으신가요?</span>
            <button
                onClick={() => navigate("/register")}
                className="ml-2 text-green-600 hover:underline text-sm"
            >
                회원가입
            </button>
            </div>
        </form>
      </div>
    </div>
  );
}
