import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIStore {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  splitSizes: [number, number];
  activeLeftTab: 'chat' | 'playground' | 'terminal';
  activeRightTab: 'logs' | 'vnc';
  
  toggleTheme: () => void;
  toggleSidebar: () => void;
  setSplitSizes: (sizes: [number, number]) => void;
  setActiveLeftTab: (tab: 'chat' | 'playground' | 'terminal') => void;
  setActiveRightTab: (tab: 'logs' | 'vnc') => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      theme: 'dark',  // 默认使用 dark 主题
      sidebarOpen: true,
      splitSizes: [50, 50],
      activeLeftTab: 'chat',
      activeRightTab: 'vnc',  // 默认打开 VNC 查看器
      
      toggleTheme: () => set(state => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),
      toggleSidebar: () => set(state => ({ sidebarOpen: !state.sidebarOpen })),
      setSplitSizes: (sizes) => set({ splitSizes: sizes }),
      setActiveLeftTab: (tab) => set({ activeLeftTab: tab }),
      setActiveRightTab: (tab) => set({ activeRightTab: tab }),
    }),
    { name: 'ui-storage' }
  )
);
