import React from "react";
import { Routes, Route, useLocation } from "react-router-dom";  // Router 빼기
import MainPage from "./Mainpage"; 
import ChatPage from "./ChatPage";
import ChatPopup from "./components/ChatPopup";
import ESGTemplatesPage from "./ESGTemplatesPage";

import ESGTemplatesListPage from "./ESGTemplatesListPage";
import EditDraftPage from "./EditDraftPage";
import LoginPage from "./LoginPage";
import RegisterPage from "./RegisterPage";
import MyPage from "./MyPage";
import SasbWritePage from "./SasbWritePage";

import Header from "./components/Header";
import EnvironmentIndicatorsPage from "./EnvironmentIndicatorsPage"; // ✅ 
import IndicatorWritePage from "./IndicatorWritePage"; // ✅ 
import SocialIndicatorsPage from "./SocialIndicatorsPage"; // ✅ 
import GovernanceIndicatorsPage from "./GovernanceIndicatorsPage"; // ✅ 
import GeneralIndicatorsPage from "./GeneralIndicatorsPage"; // ✅ 
import AppendixIndicatorsPage from "./AppendixIndicatorsPage"; // ✅ 
import EnvIndicatorGrid from "./components/EnvIndicatorGrid";

function App() {
  const location = useLocation();
  const isChatPage = location.pathname === "/chat";

  return (
    <>
      {!isChatPage && <Header />}
      <Routes>
        <Route path="/" element={<MainPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/templates" element={<ESGTemplatesPage />} />
        
        <Route path="/esg-drafts" element={<ESGTemplatesListPage />} />
        <Route path="/edit-draft" element={<EditDraftPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/mypage" element={<MyPage />} />

        <Route
          path="/indicators/environment"
          element={<EnvironmentIndicatorsPage />}
        /> // ✅ 
        <Route path="/write/indicator/:indicator_id" element={<IndicatorWritePage />} /> // ✅ 
        <Route path="/indicators/social" element={<SocialIndicatorsPage />} /> // ✅ 
        <Route path="/indicators/governance" element={<GovernanceIndicatorsPage />} /> // ✅ 
        <Route path="/indicators/general" element={<GeneralIndicatorsPage />} /> // ✅ 
        <Route path="/indicators/appendix" element={<AppendixIndicatorsPage />} /> // ✅ 
        <Route path="/write/sasb/:indicator_id" element={<SasbWritePage />} />
      </Routes>

      {!isChatPage && <ChatPopup />}
    </>
  );
}

export default App;