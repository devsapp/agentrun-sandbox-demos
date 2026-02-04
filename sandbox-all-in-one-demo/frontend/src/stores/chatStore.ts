import { create } from 'zustand';
import type { Message, ChatSession, CodeLanguage } from '@/types';
import { useSandboxStore } from './sandboxStore';
import { saveCurrentSession, loadCurrentSession } from '@/lib/storage';
import axios from 'axios';

// 全局固定会话 ID
const GLOBAL_SESSION_ID = 'global-session';

interface ChatStore {
  currentSession: ChatSession | null;
  isInitialized: boolean;
  
  // Actions
  initializeGlobalSession: () => Promise<void>;
  rebuildSession: () => Promise<void>;
  addMessage: (message: Message) => void;
  updateMessage: (messageId: string, updates: Partial<Message>) => void;
  updateSessionCode: (code: string, language?: CodeLanguage) => void;
  updateSessionSandbox: (sandboxId: string, vncUrl?: string, cdpUrl?: string, baseUrl?: string) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  currentSession: null,
  isInitialized: false,
  
  // 初始化全局会话
  initializeGlobalSession: async () => {
    try {
      // 先尝试从 localStorage 加载
      const storedSession = loadCurrentSession();
      
      if (storedSession && storedSession.session_id === GLOBAL_SESSION_ID) {
        console.log('[ChatStore] 从 localStorage 恢复会话');
        
        const session: ChatSession = {
          ...storedSession,
          created_at: storedSession.created_at,
          last_activity: Date.now(),
        };
        
        set({
          currentSession: session,
          isInitialized: true,
        });
        
        // 如果会话有 sandbox，同步到 sandboxStore
        if (storedSession.sandbox_id) {
          const sandbox = {
            sandbox_id: storedSession.sandbox_id,
            base_url: storedSession.base_url,
            vnc_url: storedSession.vnc_url,
            cdp_url: storedSession.cdp_url,
            last_access_at: Date.now(),
            log_count: 0,
          };
          useSandboxStore.setState({ currentSandbox: sandbox });
          console.log('[ChatStore] 同步 sandbox 到 sandboxStore:', sandbox);
        }
        
        return;
      }
      
      // 如果本地没有，从后端获取
      const response = await axios.get('/api/session/global');
      const sessionData = response.data;
      
      const session: ChatSession = {
        session_id: GLOBAL_SESSION_ID,
        execute_context_id: `ctx-${Date.now()}`,
        messages: [],
        code: '// JavaScript 代码\nconsole.log("Hello, World!");',
        language: 'javascript',
        sandbox_id: sessionData.sandbox_id,
        vnc_url: sessionData.vnc_url,
        cdp_url: sessionData.cdp_url,
        created_at: sessionData.created_at * 1000,
        last_activity: Date.now(),
      };
      
      set({
        currentSession: session,
        isInitialized: true,
      });
      
      // 持久化会话
      saveCurrentSession(session);
      
      console.log('[ChatStore] 全局会话已初始化:', GLOBAL_SESSION_ID);
      
      // 如果会话有 sandbox，同步到 sandboxStore
      if (sessionData.sandbox_id) {
        const sandbox = {
          sandbox_id: sessionData.sandbox_id,
          base_url: sessionData.base_url,
          vnc_url: sessionData.vnc_url,
          cdp_url: sessionData.cdp_url,
          last_access_at: Date.now(),
          log_count: 0,
        };
        useSandboxStore.setState({ currentSandbox: sandbox });
        console.log('[ChatStore] 从后端同步 sandbox 到 sandboxStore:', sandbox);
      }
    } catch (error) {
      console.error('[ChatStore] 初始化全局会话失败:', error);
      
      // 创建本地会话
      const session: ChatSession = {
        session_id: GLOBAL_SESSION_ID,
        execute_context_id: `ctx-${Date.now()}`,
        messages: [],
        code: '// JavaScript 代码\nconsole.log("Hello, World!");',
        language: 'javascript',
        created_at: Date.now(),
        last_activity: Date.now(),
      };
      
      set({
        currentSession: session,
        isInitialized: true,
      });
      
      // 持久化会话
      saveCurrentSession(session);
    }
  },
  
  // 重建会话
  rebuildSession: async () => {
    try {
      console.log('[ChatStore] 开始重建会话...');
      
      // 调用后端 API 重建会话
      const response = await axios.post('/api/session/rebuild');
      const data = response.data;
      
      // 重置本地会话
      const newSession: ChatSession = {
        session_id: GLOBAL_SESSION_ID,
        execute_context_id: `ctx-${Date.now()}`,
        messages: [],
        code: '// JavaScript 代码\nconsole.log("Hello, World!");',
        language: 'javascript',
        sandbox_id: data.sandbox_id,
        vnc_url: data.vnc_url,
        cdp_url: data.cdp_url,
        created_at: Date.now(),
        last_activity: Date.now(),
      };
      
      set({ currentSession: newSession });
      
      // 持久化新会话
      saveCurrentSession(newSession);
      
      // 更新 sandboxStore
      const sandbox = {
        sandbox_id: data.sandbox_id,
        base_url: data.base_url,
        vnc_url: data.vnc_url,
        cdp_url: data.cdp_url,
        last_access_at: Date.now(),
        log_count: 0,
      };
      
      useSandboxStore.setState({ 
        currentSandbox: sandbox,
        logs: []  // 清空日志
      });
      
      console.log('[ChatStore] 会话已重建:', data.sandbox_id);
    } catch (error) {
      console.error('[ChatStore] 重建会话失败:', error);
      throw error;
    }
  },
  
  addMessage: (message) => {
    // 防御性检查
    if (!message || !message.message_id) {
      console.warn('[ChatStore] 尝试添加无效消息，已忽略:', message);
      return;
    }
    
    set(state => {
      if (!state.currentSession) return state;
      
      // 检查消息是否已存在
      const messageExists = state.currentSession.messages.some(
        msg => msg.message_id === message.message_id
      );
      
      if (messageExists) {
        console.log(`[ChatStore] 消息 ${message.message_id} 已存在，跳过添加`);
        return state;
      }
      
      const updatedSession = {
        ...state.currentSession,
        messages: [...state.currentSession.messages, message],
        last_activity: Date.now()
      };
      
      // 持久化会话
      saveCurrentSession(updatedSession);
      
      return { currentSession: updatedSession };
    });
  },
  
  updateMessage: (messageId, updates) => {
    set(state => {
      if (!state.currentSession) return state;
      
      const updatedSession = {
        ...state.currentSession,
        messages: state.currentSession.messages.map(msg =>
          msg.message_id === messageId ? { ...msg, ...updates } : msg
        ),
      };
      
      // 持久化会话
      saveCurrentSession(updatedSession);
      
      return { currentSession: updatedSession };
    });
  },
  
  updateSessionCode: (code, language) => {
    set(state => {
      if (!state.currentSession) return state;
      
      const updatedSession: ChatSession = {
        ...state.currentSession,
        code,
        language: language || state.currentSession.language,
        last_activity: Date.now()
      };
      
      // 持久化会话
      saveCurrentSession(updatedSession);
      
      return { currentSession: updatedSession };
    });
  },
  
  updateSessionSandbox: (sandboxId, vncUrl, cdpUrl, baseUrl) => {
    set(state => {
      if (!state.currentSession) return state;
      
      const updatedSession = {
        ...state.currentSession,
        sandbox_id: sandboxId,
        base_url: baseUrl,
        vnc_url: vncUrl,
        cdp_url: cdpUrl,
        last_activity: Date.now()
      };
      
      // 持久化会话
      saveCurrentSession(updatedSession);
      
      // 同步到 sandboxStore
      const sandbox = {
        sandbox_id: sandboxId,
        base_url: baseUrl,
        vnc_url: vncUrl,
        cdp_url: cdpUrl,
        last_access_at: Date.now(),
        log_count: 0,
      };
      useSandboxStore.setState({ currentSandbox: sandbox });
      console.log('[ChatStore] 已同步 sandbox 到 sandboxStore:', sandboxId);
      
      return { currentSession: updatedSession };
    });
  },
}));
