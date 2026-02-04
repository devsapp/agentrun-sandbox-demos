import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useUIStore } from '@/stores/uiStore';

export function AppLayout() {
  const { sidebarOpen, theme } = useUIStore();
  
  // 应用深色模式到 html 元素
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);
  
  return (
      <div className="flex h-screen bg-background text-foreground">
        {sidebarOpen && <Sidebar />}
        <div className="flex-1 flex flex-col">
          <Header />
          <main className="flex-1 overflow-hidden">
            <Outlet />
          </main>
      </div>
    </div>
  );
}
