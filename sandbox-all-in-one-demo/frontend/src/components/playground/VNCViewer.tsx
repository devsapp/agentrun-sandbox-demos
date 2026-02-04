import { useEffect, useRef } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { useSandboxStore } from '@/stores/sandboxStore';
import { Monitor, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function VNCViewer() {
  const { currentSession } = useChatStore();
  const { currentSandbox } = useSandboxStore();
  const iframeRef = useRef<HTMLIFrameElement>(null);
  
  // 优先使用会话的 VNC URL，其次使用当前 sandbox 的 VNC URL
  const vncUrl = currentSession?.vnc_url || currentSandbox?.vnc_url;
  const sandboxId = currentSession?.sandbox_id || currentSandbox?.sandbox_id;
  
  // 当 VNC URL 变化时，更新 iframe 的 src 或发送 postMessage
  useEffect(() => {
    if (!vncUrl || !iframeRef.current) return;
    
    // 如果 iframe 已经加载，通过 postMessage 更新 VNC URL
    if (iframeRef.current.contentWindow) {
      iframeRef.current.contentWindow.postMessage(
        { type: 'updateVncUrl', url: vncUrl },
        '*'
      );
    }
  }, [vncUrl]);
  
  // 重新加载 iframe
  const handleReload = () => {
    if (iframeRef.current) {
      iframeRef.current.src = iframeRef.current.src;
    }
  };
  
  if (!vncUrl) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-gradient-to-br from-background to-muted/10 px-6 py-8 text-center">
        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary/20 to-primary/40 flex items-center justify-center mb-4 shadow-lg">
          <Monitor className="w-8 h-8 text-primary" />
        </div>
        <h3 className="text-lg font-semibold mb-2 text-foreground">VNC 未连接</h3>
        <p className="text-muted-foreground max-w-md text-sm mb-4">
          {currentSession 
            ? '正在为当前会话创建 Sandbox 和 VNC 连接...'
            : '请创建或选择一个会话以启动 VNC 查看器'
          }
        </p>
        <div className="text-xs text-muted-foreground/70 bg-muted/30 p-3 rounded-lg max-w-lg space-y-1.5">
          <p className="font-medium flex items-center gap-1.5">
            <span>[提示]</span>
            <span>提示</span>
          </p>
          <p>• 点击下方"新建会话"按钮创建新会话</p>
          <p>• 会话创建时会自动启动 Sandbox 并连接 VNC</p>
          <p>• VNC 连接可以让你实时查看桌面和浏览器</p>
        </div>
      </div>
    );
  }
  
  // 构建 iframe URL（使用独立的 noVNC 页面）
  const iframeUrl = `/static/vnc-iframe.html?url=${encodeURIComponent(vncUrl)}`;
  
  return (
    <div className="flex flex-col h-full bg-black relative">
      {/* 顶部工具栏 - 横向布局 */}
      <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-3 py-2 bg-gradient-to-b from-black/80 via-black/60 to-transparent pointer-events-none">
        {/* 左侧：连接状态 */}
        <div className="bg-black/70 text-white text-xs px-2.5 py-1.5 rounded-md border border-white/10 pointer-events-auto">
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-medium">已连接</span>
            <span className="opacity-60">|</span>
            <span className="opacity-80">
              {currentSession 
                ? `会话: ${currentSession.session_id.slice(-8)}`
                : `Sandbox: ${sandboxId?.slice(0, 8)}...`
              }
            </span>
          </div>
        </div>
        
        {/* 右侧：操作按钮 */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleReload}
          className="bg-black/70 border-white/20 text-white hover:bg-black/90 h-7 text-xs pointer-events-auto"
        >
          <RefreshCw className="w-3 h-3 mr-1" />
          重新加载
        </Button>
      </div>
      
      {/* noVNC iframe */}
      <iframe
        ref={iframeRef}
        src={iframeUrl}
        className="w-full h-full border-0"
        title="VNC Viewer"
        allow="fullscreen"
      />
    </div>
  );
}
