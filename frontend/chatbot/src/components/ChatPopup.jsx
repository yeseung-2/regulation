import { useState, useRef, useEffect } from "react";
import ChatPage from "../ChatPage";
import { AnimatePresence, motion } from "framer-motion";
import botImage from "../assets/chatbot_image.png";

export default function ChatPopup() {
  const [open, setOpen] = useState(false);
  const scrollRef = useRef(null);

  // ✅ 채팅 열릴 때 자동 스크롤
  useEffect(() => {
    if (open) {
      setTimeout(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 300); // 애니메이션 시간과 맞춤
    }
  }, [open]);

  return (
    <>
      {/* ✅ 채팅 팝업 */}
      <AnimatePresence>
        {open && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 50 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 50 }}
          transition={{ duration: 0.25 }}
          className="
            fixed z-50 shadow-2xl rounded-2xl overflow-hidden flex flex-col
            bottom-24 right-4 
            w-[95vw] h-[85vh] max-w-[480px] max-h-[640px]
            bg-white
          "
        >
            {/* ✅ 닫기 버튼 */}
            <div className="flex justify-between items-center p-2 border-b border-gray-200">
              <span className="font-semibold text-green-700 ml-2">ESG Report Intelligence</span>
              <button
                onClick={() => setOpen(false)}
                className="text-gray-500 hover:text-red-500 px-2 text-lg"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto">
              <ChatPage scrollRef={scrollRef} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ✅ 말풍선 버튼 */}
      <button
        onClick={() => setOpen(!open)}
        className="
          group fixed bottom-4 right-4 z-50 w-20 h-20 rounded-full 
          p-[3px] bg-gradient-to-tr from-green-400 to-emerald-500
          shadow-xl transition-all duration-300 hover:scale-105
        "
      >
        <div className="w-full h-full bg-white rounded-full flex items-center justify-center">
          <img
            src={botImage}
            alt="Chatbot"
            className="
              w-14 h-14 rounded-full object-cover transition-transform duration-300 
              group-hover:scale-110
            "
          />
        </div>
      </button>

    </>
  );
}