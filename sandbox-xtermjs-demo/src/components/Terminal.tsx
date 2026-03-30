import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';

interface TerminalStats {
  messagesSent: number;
  messagesReceived: number;
  bytesSent: number;
  bytesReceived: number;
}

const TerminalComponent: React.FC = () => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const terminalInstanceRef = useRef<Terminal | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const dataHandlerRef = useRef<((data: string) => void) | null>(null);

  const [wsUrl, setWsUrl] = useState('');
  const [inputUrl, setInputUrl] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [stats, setStats] = useState<TerminalStats>({
    messagesSent: 0,
    messagesReceived: 0,
    bytesSent: 0,
    bytesReceived: 0
  });

  // 初始化终端
  useEffect(() => {
    if (!terminalRef.current) return;

    const terminal = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Monaco, Menlo, "Ubuntu Mono", Consolas, source-code-pro, monospace',
      theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
        cursor: '#aeafad',
        selectionBackground: '#264f78',
        black: '#000000',
        red: '#cd3131',
        green: '#0dbc79',
        yellow: '#e5e510',
        blue: '#2472c8',
        magenta: '#bc3fbc',
        cyan: '#11a8cd',
        white: '#e5e5e5',
        brightBlack: '#666666',
        brightRed: '#f14c4c',
        brightGreen: '#23d18b',
        brightYellow: '#f5f543',
        brightBlue: '#3b8eea',
        brightMagenta: '#d670d6',
        brightCyan: '#29b8db',
        brightWhite: '#e5e5e5'
      },
      allowProposedApi: true,
      scrollback: 10000,
      rows: 24,
      cols: 80,
    });

    terminal.open(terminalRef.current);
    terminalInstanceRef.current = terminal;
    setIsReady(true);

    const fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);
    fitAddonRef.current = fitAddon;

    // 延迟 fit 确保容器已渲染
    setTimeout(() => {
      fitAddon.fit();
    }, 0);

    const handleResize = () => {
      fitAddonRef.current?.fit();
    };
    window.addEventListener('resize', handleResize);

    // 初始欢迎信息
    terminal.writeln('\x1b[1;34m╔══════════════════════════════════════════════════════════════╗\x1b[0m');
    terminal.writeln('\x1b[1;34m║\x1b[0m                                                        \x1b[1;34m║\x1b[0m');
    terminal.writeln('\x1b[1;34m║\x1b[0m  \x1b[1;33m欢迎使用 XTerm.js WebSocket 终端\x1b[0m       \x1b[1;34m║\x1b[0m');
    terminal.writeln('\x1b[1;34m║\x1b[0m                                                        \x1b[1;34m║\x1b[0m');
    terminal.writeln('\x1b[1;34m║\x1b[0m  请在上方工具栏输入 WebSocket URL 并点击"设置"              \x1b[1;34m║\x1b[0m');
    terminal.writeln('\x1b[1;34m║\x1b[0m  然后点击"连接"按钮建立 WebSocket 连接                     \x1b[1;34m║\x1b[0m');
    terminal.writeln('\x1b[1;34m║\x1b[0m                                                        \x1b[1;34m║\x1b[0m');
    terminal.writeln('\x1b[1;34m╚══════════════════════════════════════════════════════════════╝\x1b[0m');
    terminal.writeln('');

    return () => {
      window.removeEventListener('resize', handleResize);
      dataHandlerRef.current = null;
      fitAddonRef.current?.dispose();
      terminalInstanceRef.current?.dispose();
      terminalInstanceRef.current = null;
      wsRef.current?.close(1000, 'Component unmounted');
    };
  }, []);

  // 连接终端WebSocket
  const connectTerminal = useCallback(() => {
    if (isConnected || !wsUrl || !terminalInstanceRef.current) {
      console.warn('终端已连接或URL无效或终端未初始化');
      return;
    }

    const terminal = terminalInstanceRef.current;

    try {
      terminal.clear();
      terminal.writeln('\x1b[1;33m正在连接...\x1b[0m');

      const ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log('终端WebSocket连接成功');

        terminal.clear();
        terminal.focus();

        // 设置终端输入处理
        const dataHandler = (data: string) => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(data);
            setStats(prev => ({
              ...prev,
              messagesSent: prev.messagesSent + 1,
              bytesSent: prev.bytesSent + data.length
            }));
          }
        };

        // 移除旧的处理器
        if (dataHandlerRef.current) {
          dataHandlerRef.current = null;
        }

        dataHandlerRef.current = dataHandler;
        terminal.onData(dataHandler);
      };

      ws.onmessage = (event) => {
        let data: string;
        if (event.data instanceof ArrayBuffer) {
          data = new TextDecoder().decode(event.data);
        } else if (event.data instanceof Blob) {
          const reader = new FileReader();
          reader.onload = () => {
            const text = reader.result as string;
            terminalInstanceRef.current?.write(text);
          };
          reader.readAsText(event.data);
          return;
        } else {
          data = event.data;
        }

        terminal.write(data);
        setStats(prev => ({
          ...prev,
          messagesReceived: prev.messagesReceived + 1,
          bytesReceived: prev.bytesReceived + data.length
        }));
      };

      ws.onerror = (error) => {
        console.error('终端WebSocket连接错误:', error);
        terminal.writeln('\x1b[1;31m连接错误\x1b[0m');
        setIsConnected(false);
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        dataHandlerRef.current = null;
        terminal.writeln('');
        terminal.writeln('\x1b[1;33m连接已关闭\x1b[0m');
        if (event.code !== 1000) {
          console.warn(`终端WebSocket连接关闭: code=${event.code}, reason=${event.reason}`);
        }
      };
    } catch (error) {
      console.error('终端连接失败:', error);
      terminal.writeln('\x1b[1;31m连接失败\x1b[0m');
    }
  }, [isConnected, wsUrl]);

  // 断开终端连接
  const disconnectTerminal = useCallback(() => {
    dataHandlerRef.current = null;
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
    setIsConnected(false);
    terminalInstanceRef.current?.writeln('');
    terminalInstanceRef.current?.writeln('\x1b[1;33m已断开连接\x1b[0m');
  }, []);

  // 清空终端
  const clearTerminal = useCallback(() => {
    terminalInstanceRef.current?.clear();
  }, []);

  // 设置URL
  const handleSetUrl = useCallback(() => {
    if (inputUrl.trim()) {
      setWsUrl(inputUrl.trim());
      terminalInstanceRef.current?.clear();
      terminalInstanceRef.current?.writeln(`\x1b[1;32mURL 已设置: ${inputUrl.trim()}\x1b[0m`);
      terminalInstanceRef.current?.writeln('点击"连接"按钮开始连接...');
    }
  }, [inputUrl]);

  // 断开并重置
  const handleDisconnect = useCallback(() => {
    disconnectTerminal();
    setWsUrl('');
    setInputUrl('');
    terminalInstanceRef.current?.clear();
    terminalInstanceRef.current?.writeln('\x1b[1;33m等待新的 WebSocket URL...\x1b[0m');
  }, [disconnectTerminal]);

  return (
    <div className="terminal-wrapper">
      {/* 顶部工具栏 */}
      <div className="terminal-toolbar">
        <div className="toolbar-left">
          <span className="terminal-brand">Terminal</span>
          <div className="url-input-group">
            <input
              type="text"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="输入 WebSocket URL..."
              disabled={isConnected || !!wsUrl}
              className="url-input"
            />
            {!wsUrl ? (
              <button
                className="btn btn-connect"
                onClick={handleSetUrl}
                disabled={!inputUrl.trim()}
              >
                设置
              </button>
            ) : (
              <button
                className="btn btn-disconnect"
                onClick={handleDisconnect}
              >
                重置
              </button>
            )}
          </div>
        </div>
        <div className="toolbar-right">
          {wsUrl && (
            <>
              {isConnected ? (
                <button
                  className="btn btn-disconnect"
                  onClick={disconnectTerminal}
                >
                  断开
                </button>
              ) : (
                <button
                  className="btn btn-connect"
                  onClick={connectTerminal}
                >
                  连接
                </button>
              )}
              <button
                className="btn btn-clear"
                onClick={clearTerminal}
                disabled={!isConnected}
              >
                清空
              </button>
            </>
          )}
        </div>
      </div>

      {/* 终端主体区域 - 始终显示 */}
      <div className="terminal-main">
        <div ref={terminalRef} className="terminal-viewport" />
      </div>

      {/* 底部状态栏 */}
      <div className="terminal-statusbar">
        <div className="status-left">
          {isConnected ? (
            <>
              <span className="status-indicator connected">
                <span className="status-dot"></span>
                已连接
              </span>
              <span className="status-separator">|</span>
              <span className="status-url">{wsUrl}</span>
            </>
          ) : wsUrl ? (
            <span className="status-indicator disconnected">未连接</span>
          ) : (
            <span className="status-indicator">等待输入</span>
          )}
        </div>
        {isConnected && (
          <div className="status-right">
            <span>↑ {(stats.bytesSent / 1024).toFixed(2)} KB</span>
            <span>↓ {(stats.bytesReceived / 1024).toFixed(2)} KB</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default TerminalComponent;
