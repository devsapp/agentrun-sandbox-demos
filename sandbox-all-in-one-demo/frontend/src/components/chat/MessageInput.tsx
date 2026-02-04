import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Send, Loader2 } from 'lucide-react';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled && !isSending) {
      setIsSending(true);
      try {
        await onSend(message);
        setMessage('');
      } finally {
        setIsSending(false);
      }
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="border-t border-border bg-card/30 backdrop-blur-sm px-4 py-3">
      <div className="max-w-4xl mx-auto">
        <div className="relative flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="输入消息... (Shift+Enter 换行，Enter 发送)"
              className="w-full resize-none rounded-lg border border-input bg-background/50 px-3 py-2.5 text-sm
                focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary
                transition-all duration-200
                min-h-[44px] max-h-[160px] scrollbar-hidden"
              disabled={disabled || isSending}
              rows={1}
              style={{
                height: 'auto',
                minHeight: '44px',
                maxHeight: '160px'
              }}
            />
            {message.trim() && (
              <div className="absolute right-2 bottom-2 text-[10px] text-muted-foreground/60">
                {message.length}
              </div>
            )}
          </div>
          <Button 
            type="submit" 
            disabled={disabled || !message.trim() || isSending} 
            size="icon"
            className="h-[44px] w-[44px] rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 
              hover:from-blue-600 hover:to-purple-700 text-white shadow-md 
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-all duration-200 hover:scale-[1.02] active:scale-95"
          >
            {isSending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
        {disabled && (
          <div className="text-[10px] text-amber-400 mt-1.5 flex items-center gap-1">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
            等待连接...
          </div>
        )}
      </div>
    </form>
  );
}
