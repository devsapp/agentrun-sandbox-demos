import { Button } from '@/components/ui/button';
import { useUIStore } from '@/stores/uiStore';
import { Menu, Moon, Sun, Code2 } from 'lucide-react';

export function Header() {
  const { theme, toggleTheme, toggleSidebar } = useUIStore();
  
  return (
    <header className="border-b border-border bg-card/30 backdrop-blur-md px-4 py-3 flex items-center justify-between sticky top-0 z-10 shadow-sm">
      <div className="flex items-center gap-3">
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={toggleSidebar} 
          className="h-9 w-9"
        >
          <Menu className="w-4 h-4" />
        </Button>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center shadow-md">
            <Code2 className="w-4.5 h-4.5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-foreground">
              AI 代码生成与执行
            </h1>
            <p className="text-xs text-muted-foreground">智能编程助手</p>
          </div>
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        <Button 
          variant="outline" 
          size="icon" 
          onClick={toggleTheme}
          className="h-9 w-9 border-border hover:bg-accent"
          title={theme === 'light' ? '切换到深色模式' : '切换到浅色模式'}
        >
          {theme === 'light' ? (
            <Moon className="w-4 h-4" />
          ) : (
            <Sun className="w-4 h-4" />
          )}
        </Button>
      </div>
    </header>
  );
}
