import { create } from 'zustand';
import type { Sandbox, LogEntry } from '@/types';
import axios from 'axios';
import { 
  saveCurrentSandbox, 
  loadCurrentSandbox
} from '@/lib/storage';

interface SandboxStore {
  currentSandbox: Sandbox | null;
  logs: LogEntry[];
  wsConnected: boolean;
  isCreatingSandbox: boolean;
  isInitialized: boolean;
  
  // Actions
  initializeFromStorage: () => void;
  createSandbox: (sessionId: string) => Promise<Sandbox | null>;
  setCurrentSandbox: (sandbox: Sandbox | null) => void;
  addLog: (log: LogEntry) => void;
  clearLogs: () => void;
}

export const useSandboxStore = create<SandboxStore>((set) => ({
  currentSandbox: null,
  logs: [],
  wsConnected: false,
  isCreatingSandbox: false,
  isInitialized: false,
  
  // 从 localStorage 初始化当前 sandbox
  initializeFromStorage: () => {
    const storedSandbox = loadCurrentSandbox();
    
    set({
      currentSandbox: storedSandbox,
      isInitialized: true,
    });
    
    if (storedSandbox) {
      console.log('[SandboxStore] 从 localStorage 加载了 sandbox:', storedSandbox.sandbox_id);
    } else {
      console.log('[SandboxStore] localStorage 中没有 sandbox 数据');
    }
  },
  
  createSandbox: async (sessionId: string) => {
    set({ isCreatingSandbox: true });
    try {
      // 调用后端 API 创建 sandbox
      const response = await axios.post('/api/sandbox/create', {
        session_id: sessionId,
        enable_vnc: true,  // 启用 VNC
      });
      
      const newSandbox: Sandbox = response.data;
      
      // 更新状态并持久化
      set({
        currentSandbox: newSandbox,
        isCreatingSandbox: false,
      });
      
      saveCurrentSandbox(newSandbox);
      
      return newSandbox;
    } catch (error) {
      console.error('Failed to create sandbox:', error);
      set({ isCreatingSandbox: false });
      return null;
    }
  },
  
  setCurrentSandbox: (sandbox) => {
    set({ currentSandbox: sandbox, logs: [] });
    
    // 持久化当前 sandbox
    if (sandbox) {
      const updatedSandbox = {
        ...sandbox,
        last_access_at: Date.now()
      };
      saveCurrentSandbox(updatedSandbox);
    } else {
      saveCurrentSandbox(null);
    }
  },
  
  addLog: (log) => {
    set(state => ({ logs: [...state.logs, log] }));
  },
  
  clearLogs: () => {
    set({ logs: [] });
  },
}));
