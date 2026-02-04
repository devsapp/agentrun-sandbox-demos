import { useEffect, useState, useRef } from 'react';
import { useSandboxStore } from '@/stores/sandboxStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { WS_BASE_URL } from '@/lib/api/client';
import { Button } from '@/components/ui/button';
import { Trash2, Download, ScrollText, ChevronDown, ChevronUp } from 'lucide-react';
import Convert from 'ansi-to-html';
import { ScrollArea } from '@/components/ui/scroll-area';

interface LogViewerProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export function LogViewer({ isCollapsed, onToggleCollapse }: LogViewerProps) {
  const { currentSandbox, logs, addLog, clearLogs } = useSandboxStore();
  const [logEntries, setLogEntries] = useState<Array<{ html: string; timestamp: string }>>([]);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const converterRef = useRef<Convert>(new Convert({
    fg: '#FFF',
    bg: '#000',
    newline: false,
    escapeXML: true,
    stream: false,
  }));
  
  //  添加调试信息
  useEffect(() => {
    console.log('[LogViewer] currentSandbox 变化:', currentSandbox);
    console.log('[LogViewer] sandbox_id:', currentSandbox?.sandbox_id);
    console.log('[LogViewer] WebSocket URL:', currentSandbox ? `${WS_BASE_URL}/ws/log/${currentSandbox.sandbox_id}` : 'null');
  }, [currentSandbox]);
  
  // 连接 WebSocket 接收实时日志
  const { isConnected } = useWebSocket(
    currentSandbox ? `${WS_BASE_URL}/ws/log/${currentSandbox.sandbox_id}` : null,
    {
      onMessage: (data) => {
        console.log('[LogViewer] 收到日志消息:', data);
        if (data.type === 'log') {
          const timestamp = new Date(data.timestamp * 1000).toLocaleTimeString();
          const converter = converterRef.current;
          const html = converter.toHtml(data.message);
          
          setLogEntries(prev => [...prev, { html, timestamp }]);
          addLog(data);
          
          // 自动滚动到底部
          setTimeout(() => {
            if (logContainerRef.current) {
              logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
            }
          }, 10);
        }
      },
      onOpen: () => {
        console.log('[LogViewer] WebSocket 连接成功:', currentSandbox?.sandbox_id);
      },
      onClose: () => {
        console.log('[LogViewer] WebSocket 连接关闭:', currentSandbox?.sandbox_id);
      },
      onError: (error) => {
        console.error('[LogViewer] WebSocket 错误:', error, 'sandbox_id:', currentSandbox?.sandbox_id);
      },
    }
  );
  
  // 初始加载历史日志
  useEffect(() => {
    console.log('[LogViewer] 历史日志数量:', logs.length);
    if (logs.length > 0) {
      const converter = converterRef.current;
      const historicalLogs = logs.map(log => ({
        html: converter.toHtml(log.message),
        timestamp: new Date(log.timestamp * 1000).toLocaleTimeString(),
      }));
      setLogEntries(historicalLogs);
    } else {
      //  当切换到没有日志的 sandbox 时，清空显示
      setLogEntries([]);
    }
  }, [logs, currentSandbox?.sandbox_id]);  //  添加 currentSandbox?.sandbox_id 依赖
  
  // 监听 currentSandbox 变化
  useEffect(() => {
    console.log('[LogViewer] currentSandbox 变化:', currentSandbox?.sandbox_id);
    console.log('[LogViewer] WebSocket 连接状态:', isConnected);
  }, [currentSandbox, isConnected]);
  
  const handleClearLogs = () => {
    setLogEntries([]);
    clearLogs();
  };
  
  const handleDownloadLogs = () => {
    const plainText = logEntries.map(entry => 
      `[${entry.timestamp}] ${entry.html.replace(/<[^>]*>/g, '')}`
    ).join('\n');
    const blob = new Blob([plainText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-${currentSandbox?.sandbox_id || 'unknown'}-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };
  
  // 统一的工具栏组件
  const toolbar = (
    <div className="border-b border-border bg-card/30 backdrop-blur-sm px-3 py-2 flex justify-between items-center">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <ScrollText className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="text-sm font-medium">执行日志</span>
        </div>
        {!isCollapsed && currentSandbox && (
          <>
            <span className="text-xs text-muted-foreground">
              {isConnected ? '[OK] 已连接' : '[CRITICAL] 未连接'}
            </span>
            <span className="text-xs text-muted-foreground">
              {logEntries.length} 条
            </span>
          </>
        )}
      </div>
      <div className="flex gap-1">
        {!isCollapsed && currentSandbox && (
          <>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={handleDownloadLogs} 
              className="h-6 text-xs px-2"
              title="下载日志"
            >
              <Download className="w-3.5 h-3.5 mr-1" />
              下载
            </Button>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={handleClearLogs} 
              className="h-6 text-xs px-2"
              title="清空日志"
            >
              <Trash2 className="w-3.5 h-3.5 mr-1" />
              清空
            </Button>
          </>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCollapse}
          className="h-6 px-2 text-xs"
          title={isCollapsed ? "展开日志" : "折叠日志"}
        >
          {isCollapsed ? (
            <>
              <ChevronUp className="w-3.5 h-3.5 mr-1" />
              展开
            </>
          ) : (
            <>
              <ChevronDown className="w-3.5 h-3.5 mr-1" />
              折叠
            </>
          )}
        </Button>
      </div>
    </div>
  );

  // 折叠状态：只显示工具栏
  if (isCollapsed) {
    return (
      <div className="flex flex-col">
        {toolbar}
      </div>
    );
  }

  // 展开状态：显示工具栏 + 日志内容
  if (!currentSandbox) {
    return (
      <div className="flex flex-col h-full bg-background">
        {toolbar}
        <div className="flex-1 flex items-center justify-center text-muted-foreground/60 text-xs px-4">
          <div className="text-center space-y-2">
            <p>正在等待 Sandbox 初始化...</p>
            <p className="text-[10px]">发送消息或执行代码将自动创建 Sandbox</p>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="flex flex-col h-full bg-background">
      {toolbar}
      
      {/* 日志查看器 */}
      <ScrollArea className="flex-1">
        <div 
          ref={logContainerRef}
          className="p-2 space-y-1 font-mono text-xs"
          style={{
            backgroundColor: 'hsl(var(--background))',
            minHeight: '100%',
          }}
        >
          {logEntries.length > 0 ? (
            logEntries.map((entry, index) => (
              <div 
                key={index} 
                className="log-line flex gap-2 hover:bg-muted/30"
                style={{ lineHeight: '1.5' }}
              >
                <span className="text-muted-foreground shrink-0">
                  [{entry.timestamp}]
                </span>
                <span 
                  dangerouslySetInnerHTML={{ __html: entry.html }}
                  className="ansi-output flex-1"
                />
              </div>
            ))
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground/60 text-xs py-20">
              <div className="text-center space-y-1">
                <p>暂无日志</p>
                <p className="text-[10px]">执行代码后将显示日志</p>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
