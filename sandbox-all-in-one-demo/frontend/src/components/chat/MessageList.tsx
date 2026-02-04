import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageBubble } from './MessageBubble';
import type { Message } from '@/types';

interface MessageListProps {
  messages: Message[];
}

export function MessageList({ messages }: MessageListProps) {
  return (
    <ScrollArea className="flex-1 px-4 py-3">
      <div className="space-y-3 max-w-4xl mx-auto">
        {messages.filter(msg => msg && msg.message_id).map(message => (
          <MessageBubble key={message.message_id} message={message} />
        ))}
      </div>
    </ScrollArea>
  );
}
