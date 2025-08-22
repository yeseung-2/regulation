import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import logo from "/src/assets/chatbot_image.png";

export default function Header() {
  const [activeMenu, setActiveMenu] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const isMainPage = location.pathname === "/";

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    setIsLoggedIn(!!token);
  }, []);

  const menuItems = [
    {
      title: "보고서 작성",
      subItems: ["• 환경", "• 사회", "• 지배구조", "• 일반", "• 부록", "• 보고서 최종 생성"],
    },
    {
      title: "규정안 작성",
      subItems: ["• ESG 규정 목록", "• ESG 규정 작성"],
    },
  ];

  const getMenuStyle = (base, hover) =>
    `${base} text-sm font-semibold transition ${hover}`;

  return (
    <header
      className={`fixed top-0 left-0 w-full z-[100] transition-all duration-700 overflow-hidden ${
        isMainPage
          ? "bg-black bg-opacity-40 text-white"
          : "bg-white border-b shadow text-gray-800"
      }`}
      style={{ maxHeight: activeMenu ? "260px" : "64px" }}
      
      onMouseLeave={() => setActiveMenu(null)}
    >
      {/* 상단 바 */}
      <div className="max-w-screen-xl mx-auto px-6 py-3 flex justify-between items-center">
        <div
          className={`flex items-center gap-2 font-bold text-xl cursor-pointer ${
            isMainPage ? "text-white" : "text-green-800"
          }`}
          onClick={() => navigate("/")}
        >
          <img src={logo} className="w-8 h-8 rounded-full" alt="logo" />
          ERI
        </div>
        <nav className="flex gap-8">
          {menuItems.map((item) => (
            <button
              key={item.title}
              className={getMenuStyle(
                isMainPage ? "text-white" : "text-gray-700",
                isMainPage ? "hover:text-green-300" : "hover:text-green-600"
              )}
              onMouseEnter={() => setActiveMenu(item)}
            >
              {item.title}
            </button>
          ))}
          {isLoggedIn ? (
            <>
              <button
                className={getMenuStyle(
                  isMainPage ? "text-white" : "text-gray-700",
                  isMainPage ? "hover:text-green-300" : "hover:text-green-600"
                )}
                onClick={() => navigate("/mypage")}
              >
                마이페이지
              </button>
              <button
                className={getMenuStyle(
                  isMainPage ? "text-red-300" : "text-red-500",
                  isMainPage ? "hover:text-red-500" : "hover:text-red-700"
                )}
                onClick={() => {
                  localStorage.removeItem("access_token");
                  navigate("/login");
                }}
              >
                로그아웃
              </button>
            </>
          ) : (
            <button
              className={getMenuStyle(
                isMainPage ? "text-white" : "text-gray-700",
                isMainPage ? "hover:text-green-300" : "hover:text-green-600"
              )}
              onClick={() => navigate("/login")}
            >
              로그인
            </button>
          )}
        </nav>
      </div>

      {/* 드롭다운 메뉴 */}
      {activeMenu && (
        <div
          className={`w-full border-t ${
            isMainPage ? "bg-black bg-opacity-60" : "bg-white"
          }`}
        >
          <div className="max-w-screen-xl mx-auto px-6 py-4 grid grid-cols-3 gap-y-3 gap-x-6">
            {activeMenu.subItems.map((sub, i) => (
              <div
                key={i}
                className={`text-sm cursor-pointer px-2 py-1 rounded ${sub.includes("보고서 최종 생성")
                  ? isMainPage
                    ? "text-green-200 font-semibold"
                    : "text-green-600 font-semibold"
                  : isMainPage
                  ? "text-white hover:text-green-300"
                  : "text-gray-700 hover:text-green-600"}

                }`}
                onClick={() => {
                  if (sub.includes("환경")) navigate("/indicators/environment");
                  else if (sub.includes("사회")) navigate("/indicators/social");
                  else if (sub.includes("지배구조")) navigate("/indicators/governance");
                  else if (sub.includes("일반")) navigate("/indicators/general");
                  else if (sub.includes("부록")) navigate("/indicators/appendix");
                  else if (sub.includes("보고서 최종 생성")) navigate("/indicators/final");
                  else if (sub.includes("ESG 규정 작성")) navigate("/templates");
                  else if (sub.includes("ESG 규정 목록")) navigate("/esg-drafts");
                }}
              >
                {sub}
              </div>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}