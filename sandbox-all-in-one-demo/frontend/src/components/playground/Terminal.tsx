import { useEffect, useRef, useState, useCallback } from 'react';
import { Terminal as XTerm } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import 'xterm/css/xterm.css';
import { useSandboxStore } from '@/stores/sandboxStore';
import { useUIStore } from '@/stores/uiStore';
import { Button } from '@/components/ui/button';
import { X, AlertCircle } from 'lucide-react';

export function Terminal() {
  const { currentSandbox } = useSandboxStore();
  const { activeLeftTab } = useUIStore();
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 初始化终端
  useEffect(() => {
    if (!terminalRef.current) return;

    // 创建终端实例
    const xterm = new XTerm({
      cursorBlink: true,
      fontSize: 13,
      fontFamily: 'ui-monospace, SFMono-Regular, SF Mono, Consolas, Liberation Mono, Menlo, monospace',
      theme: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        cursor: 'hsl(var(--primary))',
        cursorAccent: 'hsl(var(--primary-foreground))',
        selectionBackground: 'hsl(var(--muted))',
      },
      rows: 30,
      cols: 100,
    });

    // 添加插件
    const fitAddon = new FitAddon();
    const webLinksAddon = new WebLinksAddon();
    xterm.loadAddon(fitAddon);
    xterm.loadAddon(webLinksAddon);

    // 打开终端
    xterm.open(terminalRef.current);
    
    // 使用 requestAnimationFrame 确保 DOM 已渲染
    requestAnimationFrame(() => {
      try {
        fitAddon.fit();
      } catch (err) {
        console.error('[Terminal] fitAddon.fit() 失败:', err);
        // 如果 fit 失败，稍后重试
        setTimeout(() => {
          try {
            fitAddon.fit();
          } catch (retryErr) {
            console.error('[Terminal] fitAddon.fit() 重试失败:', retryErr);
          }
        }, 100);
      }
    });

    xtermRef.current = xterm;
    fitAddonRef.current = fitAddon;

    // 监听窗口大小变化
    const handleResize = () => {
      try {
        fitAddon.fit();
      } catch (err) {
        console.error('[Terminal] handleResize fit 失败:', err);
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      xterm.dispose();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // 连接到远程终端
  const connectTerminal = useCallback(() => {
    if (!currentSandbox || !xtermRef.current) {
      console.log('[Terminal] 连接条件不满足:', { 
        hasSandbox: !!currentSandbox, 
        hasXterm: !!xtermRef.current 
      });
      return;
    }

    // 如果已经在连接中，不要重复连接
    if (isConnecting) {
      console.log('[Terminal] 已经在连接中，跳过');
      return;
    }

    // 如果已经连接且 WebSocket 正常，不要重复连接
    if (isConnected && wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[Terminal] 已经连接，跳过');
      return;
    }

    // 关闭旧连接
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // 重置状态
    setError(null);
    setIsConnected(false);
    setIsConnecting(true);
    
    const xterm = xtermRef.current;

    try {
      // 构建 WebSocket URL
      // 根据 API 文档，使用 protocol=text 以兼容 xterm.js
      
      let wsUrl: string;
      
      if (currentSandbox.base_url) {
        // 检查是否为本地模式
        if (currentSandbox.base_url.includes('localhost:5000') || 
            currentSandbox.base_url.includes('localhost') ||
            currentSandbox.base_url.includes('127.0.0.1')) {
          // 本地模式：直接使用 localhost:5000/processes/tty
          wsUrl = 'ws://localhost:5000/processes/tty?protocol=text';
          console.log('[Terminal] 本地模式，使用本地 TTY WebSocket:', wsUrl);
        } else {
          // 远程模式：使用完整的 base_url 构建 WebSocket URL
          // base_url 格式: https://xxx.aliyuncs.com/sandboxes/01KFZ9YQ18R9KR9ZS6W3NXNV1A
          const baseUrl = currentSandbox.base_url.replace(/^https?/, 'wss');
          
          // 从 base_url 中提取 tenantId（如果有）
          const urlMatch = baseUrl.match(/wss?:\/\/(\d+)\./);
          const tenantId = urlMatch ? urlMatch[1] : '';
          
          // 构建完整的 TTY WebSocket URL
          wsUrl = `${baseUrl}/processes/tty?protocol=text`;
          if (tenantId) {
            wsUrl += `&tenantId=${tenantId}`;
          }
          console.log('[Terminal] 远程模式，使用远程 TTY WebSocket:', wsUrl);
        }
      } else {
        // 没有 base_url，尝试使用 vnc_url 或 cdp_url 判断模式
        const vncUrl = currentSandbox.vnc_url || '';
        const cdpUrl = currentSandbox.cdp_url || '';
        
        if (vncUrl.includes('localhost:5000') || 
            cdpUrl.includes('localhost:5000') ||
            vncUrl.includes('localhost') ||
            cdpUrl.includes('localhost')) {
          // 本地模式
          wsUrl = 'ws://localhost:5000/processes/tty?protocol=text';
          console.log('[Terminal] 本地模式（从 vnc_url/cdp_url 判断），使用本地 TTY WebSocket:', wsUrl);
        } else if (vncUrl || cdpUrl) {
          // 远程模式：从 vnc_url 或 cdp_url 提取域名
          const urlToUse = vncUrl || cdpUrl;
          const match = urlToUse.match(/wss?:\/\/(.+?)\/sandboxes\/(.+?)\//);
          if (match) {
            const domain = match[1];
            const sandboxId = match[2];
            wsUrl = `wss://${domain}/sandboxes/${sandboxId}/processes/tty?protocol=text`;
            
            // 提取 tenantId
            const tenantMatch = domain.match(/^(\d+)\./);
            if (tenantMatch) {
              wsUrl += `&tenantId=${tenantMatch[1]}`;
            }
            console.log('[Terminal] 远程模式（从 vnc_url/cdp_url 提取），使用远程 TTY WebSocket:', wsUrl);
          } else {
            // 无法提取，使用默认本地地址
            wsUrl = 'ws://localhost:5000/processes/tty?protocol=text';
            console.warn('[Terminal] 无法从 vnc_url/cdp_url 提取域名，回退到本地模式');
          }
        } else {
          // 完全无法判断，使用默认本地地址
          wsUrl = 'ws://localhost:5000/processes/tty?protocol=text';
          console.warn('[Terminal] 无 base_url、vnc_url、cdp_url，回退到本地模式');
        }
      }
      
      console.log('[Terminal] 尝试连接到:', wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[Terminal] WebSocket 连接成功');
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        xterm.clear();

        // 发送终端尺寸
        if (fitAddonRef.current) {
          const { cols, rows } = xterm;
          console.log(`[Terminal] 终端尺寸: ${cols}x${rows}`);
        }
      };

      ws.onmessage = (event) => {
        xterm.write(event.data);
      };

      ws.onerror = (error) => {
        console.error('[Terminal] WebSocket 错误:', error);
        setError('连接错误');
        setIsConnected(false);
        setIsConnecting(false);
      };

      ws.onclose = (event) => {
        console.log('[Terminal] WebSocket 连接关闭', event.code, event.reason);
        setIsConnected(false);
        setIsConnecting(false);
        
        // 只在非正常关闭时显示错误
        if (event.code !== 1000 && event.code !== 1005) {
          setError(`连接已断开 (${event.code})`);
        }
      };

      // 监听终端输入
      const disposable = xterm.onData((data) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(data);
        }
      });

      // 清理函数
      return () => {
        disposable.dispose();
      };
    } catch (err) {
      console.error('[Terminal] 连接失败:', err);
      setError(err instanceof Error ? err.message : '连接失败');
      setIsConnected(false);
      setIsConnecting(false);
    }
  }, [currentSandbox, isConnecting, isConnected]);

  // 统一的自动连接逻辑
  useEffect(() => {
    // 只在终端 tab 激活时才尝试连接
    if (activeLeftTab !== 'terminal') {
      console.log('[Terminal] 不在终端tab，跳过自动连接');
      return;
    }

    // 必须有 sandbox 和 xterm 实例
    if (!currentSandbox || !xtermRef.current) {
      console.log('[Terminal] sandbox 或 xterm 未就绪');
      return;
    }

    // 如果已经连接，跳过
    if (isConnected && wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[Terminal] 已连接，跳过自动连接');
      return;
    }

    console.log('[Terminal] 触发自动连接，sandbox_id:', currentSandbox.sandbox_id);

    // 延迟连接，确保 DOM 完全渲染
    const timer = setTimeout(() => {
      // 重新调整终端尺寸
      if (fitAddonRef.current) {
        try {
          fitAddonRef.current.fit();
        } catch (err) {
          console.error('[Terminal] 自动连接前 fit 失败:', err);
        }
      }
      connectTerminal();
    }, 300);
    
    return () => {
      console.log('[Terminal] 清理自动连接定时器');
      clearTimeout(timer);
    };
  }, [activeLeftTab, currentSandbox?.sandbox_id, isConnected, connectTerminal]);

  // 清屏
  const handleClear = () => {
    if (xtermRef.current) {
      xtermRef.current.clear();
    }
  };

  if (!currentSandbox) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-muted-foreground/60 text-sm px-4">
        <AlertCircle className="w-8 h-8 mb-2 opacity-50" />
        <p>请先创建或选择一个会话</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-background">
      {/* 工具栏 */}
      <div className="border-b border-border bg-card/30 backdrop-blur-sm px-3 py-2 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium">终端</span>
          <span className="text-xs text-muted-foreground">
            {isConnecting ? '[WARN] 连接中...' : isConnected ? '[OK] 已连接' : '[CRITICAL] 未连接'}
          </span>
          {error && !isConnected && (
            <span className="text-xs text-destructive">
              [WARNING] {error}
            </span>
          )}
        </div>
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            className="h-6 px-2 text-xs"
            title="清屏"
            disabled={!xtermRef.current}
          >
            <X className="w-3.5 h-3.5 mr-1" />
            清屏
          </Button>
        </div>
      </div>

      {/* 终端显示区域 */}
      <div 
        ref={terminalRef} 
        className="flex-1 overflow-hidden p-2"
        style={{ backgroundColor: 'hsl(var(--background))' }}
      />
    </div>
  );
}
