import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { ChatPage } from '@/pages/ChatPage';
import { SessionsPage } from '@/pages/SessionsPage';
import { ViewerPage } from '@/pages/ViewerPage';
import { useSandboxStore } from '@/stores/sandboxStore';
import { useChatStore } from '@/stores/chatStore';

export default function App() {
  const initializeSandboxFromStorage = useSandboxStore(state => state.initializeFromStorage);
  const initializeGlobalSession = useChatStore(state => state.initializeGlobalSession);
  
  // 应用启动时初始化全局会话
  useEffect(() => {
    // 初始化全局会话（会从后端获取会话信息）
    initializeGlobalSession();
    // 初始化 sandbox store
    initializeSandboxFromStorage();
  }, [initializeGlobalSession, initializeSandboxFromStorage]);
  
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Navigate to="/chat" replace />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="sessions" element={<SessionsPage />} />
          <Route path="viewer/:sandboxId" element={<ViewerPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
