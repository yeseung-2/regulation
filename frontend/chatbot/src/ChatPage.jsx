import React, { useState, useRef, useEffect } from "react";
import Header from "./components/Header";
import ChatPopup from "./components/ChatPopup";
import botImage from "./assets/chatbot_image.png";
import userImage from "./assets/user_image.png";
import axios from "axios";

function ChatPage() {
  const [msg, setMsg] = useState("");
  const [chat, setChat] = useState([]);
  const endRef = useRef(null);

  const send = async () => {
    if (!msg.trim()) return;
    const userMsg = msg;
    setChat((prev) => [...prev, { role: "user", text: userMsg }]);
    setMsg("");

    try {
      const res = await axios.post("http://localhost:8000/chat/rag", {
        message: userMsg,
      });

      let botText = res.data.answer.replace(/\n/g, "<br/>");
      if (res.data.table_html) {
        botText += `<br><br><b>📊 관련 표</b><br>` + res.data.table_html;
      }

      setChat((prev) => [
        ...prev,
        {
          role: "bot",
          text: botText,
          griOriginal: res.data.gri_original || null,
          table_html: res.data.table_html,
          suggestions: res.data.suggested_questions || [],
        }
      ]);
    } catch (err) {
      setChat((prev) => [
        ...prev,
        { role: "bot", text: "⚠️ 서버 오류가 발생했습니다." }
      ]);
    }
  };

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat]);

return (
  <>
    <Header />

    <main className="pt-[130px] bg-gray-50 min-h-screen">
      <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-lg p-6 flex flex-col min-h-[80vh]">
        {/* 🌱 상단 타이틀 */}
        <div className="text-lg font-semibold text-green-800 mb-4 flex items-center gap-2 border-b pb-2">
          🌱 에리(ERI) <span className="text-xs text-gray-400 ml-auto">ESG 보고서 작성 도우미</span>
        </div>

        {/* 💬 채팅 내용 */}
        <div className="flex-1 space-y-4 overflow-y-auto mb-4 pr-1">
          {chat.map((c, i) => (
            <div
              key={i}
              className={`p-3 max-w-[80%] text-sm shadow-sm ${
                c.role === "user"
                  ? "bg-white text-gray-800 ml-auto rounded-xl border border-gray-200"
                  : "bg-green-50 text-gray-900 rounded-xl border border-green-200"
              }`}
            >
              <div className="text-xs text-gray-500 mb-1 flex items-center gap-2">
                <img
                  src={c.role === "user" ? userImage : botImage}
                  alt={c.role}
                  className={`w-8 h-8 rounded-full bg-white ring-1 ${
                    c.role === "user" ? "ring-gray-300" : "ring-green-300"
                  } p-1`}
                />
                {c.role === "user" ? "나" : "ERI"}
              </div>

              <div className="overflow-x-auto">
                <div
                  className="
                    prose max-w-none text-sm
                    [&_h3]:font-bold
                    [&_h3]:text-green-800
                    [&_h3]:text-base
                    [&_h3]:mt-4
                    [&_table]:w-full
                    [&_table]:table-auto
                    [&_table]:border
                    [&_table]:border-gray-300
                    [&_table]:rounded-md
                    [&_table]:overflow-hidden
                    [&_table]:mb-6
                    [&_thead_th]:bg-green-100
                    [&_thead_th]:text-green-900
                    [&_thead_th]:font-semibold
                    [&_thead_th]:text-center
                    [&_thead_th]:text-sm
                    [&_thead_th]:px-5
                    [&_thead_th]:py-3
                    [&_tbody_td]:px-5
                    [&_tbody_td]:py-3
                    [&_tbody_td]:border-t
                    [&_tbody_td]:text-left
                    [&_tbody_td]:text-sm
                    [&_tbody_td]:text-gray-800
                    [&_tr]:align-top
                    [&_tr:nth-child(even)]:bg-gray-50
                    [&_td]:leading-relaxed
                  "
                  dangerouslySetInnerHTML={{ __html: c.text }}
                />
              </div>

              {c.suggestions?.length > 0 && (
                <div className="mt-3 bg-green-50 border border-green-200 p-3 rounded-md">
                  <div className="text-green-800 font-semibold mb-2">💡 추천 질문</div>
                  <div className="grid grid-cols-2 gap-2">
                    {c.suggestions.map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          setMsg(q);
                          setTimeout(() => send(), 100);
                        }}
                        className="bg-green-100 text-green-800 px-3 py-1 rounded-md text-sm hover:bg-green-200"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
          <div ref={endRef} />
        </div>

        {/* ✏️ 입력창 */}
        <div className="flex gap-2 mt-auto">
          <input
            className="flex-1 px-4 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-300"
            value={msg}
            onChange={(e) => setMsg(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="메시지를 입력하세요"
          />
          <button
            onClick={send}
            className="bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold px-5 py-2 rounded-xl shadow-md hover:shadow-xl hover:from-green-600 hover:to-emerald-600 active:scale-95 transition-all duration-200"
          >
            전송
          </button>
        </div>
      </div>
    </main>

    <ChatPopup />
  </>
);
}

export default ChatPage;
