import { useEffect, useRef } from 'react';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { useChatStore } from '@/stores/chatStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { WS_BASE_URL } from '@/lib/api/client';
import { Loader2 } from 'lucide-react';

export function ChatPanel() {
  const { currentSession, addMessage } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const { isConnected, send } = useWebSocket(
    currentSession ? `${WS_BASE_URL}/ws/chat/${currentSession.session_id}` : null,
    {
      onMessage: (data) => {
        if (data.type === 'message') {
          addMessage(data.data);
        }
      },
    }
  );
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [currentSession?.messages]);
  
  const handleSendMessage = (content: string) => {
    if (!currentSession) return;
    
    // 只发送到服务器，不在前端添加（避免重复）
    // 服务器会通过 WebSocket 广播消息回来
    send({ type: 'message', content });
  };
  
  if (!currentSession) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-6 py-8 bg-gradient-to-br from-background to-muted/20">
        <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
        <h2 className="text-lg font-semibold mb-2 text-foreground">
          正在初始化全局会话...
        </h2>
        <p className="text-muted-foreground text-sm max-w-md">
          请稍候，系统正在准备对话环境
        </p>
      </div>
    );
  }
  
  return (
    <div className="flex flex-col h-full bg-background">
      {/* 连接状态指示器 */}
      {!isConnected && (
        <div className="bg-amber-500/10 text-amber-400 px-3 py-2 text-xs flex items-center gap-2 border-b border-amber-500/20">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
          正在连接到服务器...
        </div>
      )}
      
      <MessageList messages={currentSession.messages} />
      <div ref={messagesEndRef} />
      <MessageInput onSend={handleSendMessage} disabled={!isConnected} />
    </div>
  );
}
