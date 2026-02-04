import { Card } from '@/components/ui/card';
import type { Message } from '@/types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { User, Bot } from 'lucide-react';
import { ExecutableCodeBlock } from './ExecutableCodeBlock';
import { useChatStore } from '@/stores/chatStore';

interface MessageBubbleProps {
  message: Message;
}

// 解析消息中的代码块
function parseCodeBlocks(content: string) {
  const blocks: Array<{
    type: 'text' | 'code';
    content: string;
    language?: string;
    stepTitle?: string;
  }> = [];

  let lastIndex = 0;
  
  // 首先尝试匹配所有代码块（包括带步骤标题和不带标题的）
  const codeBlockPattern = /```(\w+)?\n([\s\S]*?)```/g;
  let match;
  
  while ((match = codeBlockPattern.exec(content)) !== null) {
    // 添加代码块之前的文本
    if (match.index > lastIndex) {
      const textContent = content.substring(lastIndex, match.index).trim();
      if (textContent) {
        // 检查文本末尾是否有步骤标题
        const stepTitleMatch = textContent.match(/###\s+步骤\s+\d+[：:]\s*([^\n]+)\s*$/);
        if (stepTitleMatch) {
          // 有步骤标题，分离出来
          const textBeforeTitle = textContent.substring(0, stepTitleMatch.index).trim();
          if (textBeforeTitle) {
            blocks.push({ type: 'text', content: textBeforeTitle });
          }
          // 将步骤标题作为下一个代码块的标题
          const stepTitle = stepTitleMatch[1].trim();
          blocks.push({
            type: 'code',
            content: match[2].trim(),
            language: match[1] || 'javascript',
            stepTitle,
          });
        } else {
          // 没有步骤标题，正常处理
          blocks.push({ type: 'text', content: textContent });
          blocks.push({
            type: 'code',
            content: match[2].trim(),
            language: match[1] || 'javascript',
          });
        }
      } else {
        // 没有文本，直接添加代码块
        blocks.push({
          type: 'code',
          content: match[2].trim(),
          language: match[1] || 'javascript',
        });
      }
    } else {
      // 从开头就是代码块
      blocks.push({
        type: 'code',
        content: match[2].trim(),
        language: match[1] || 'javascript',
      });
    }
    
    lastIndex = match.index + match[0].length;
  }

  // 添加最后剩余的文本
  if (lastIndex < content.length) {
    const remainingText = content.substring(lastIndex).trim();
    if (remainingText) {
      blocks.push({ type: 'text', content: remainingText });
    }
  }

  // 如果没有解析到任何内容，返回整个文本
  if (blocks.length === 0) {
    blocks.push({ type: 'text', content });
  }

  return blocks;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const currentSession = useChatStore((state) => state.currentSession);
  
  // 解析代码块
  const contentBlocks = isUser ? [{ type: 'text' as const, content: message.content }] : parseCodeBlocks(message.content);
  
  // 如果消息包含 language 字段，应用到所有代码块
  const blocksWithLanguage = contentBlocks.map(block => {
    if (block.type === 'code' && message.language && !block.language) {
      return { ...block, language: message.language };
    }
    return block;
  });
  
  return (
    <div className={`flex gap-2.5 ${isUser ? 'flex-row-reverse' : 'flex-row'} group fade-in`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${
        isUser 
          ? 'bg-blue-500' 
          : 'bg-gradient-to-br from-emerald-500 to-teal-600'
      } shadow-sm`}>
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>
      
      {/* Message Content */}
      <div className="flex-1 max-w-3xl">
        <div className={`text-[10px] text-muted-foreground/70 mb-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {isUser ? '你' : 'AI 助手'}
        </div>
        <Card className={`px-3 py-2.5 shadow-sm ${
          isUser 
            ? 'bg-card/50 border-border/50 backdrop-blur-sm' 
            : 'bg-card/50 border-border/50 backdrop-blur-sm'
        }`}>
          {blocksWithLanguage.map((block, index) => (
            <div key={index}>
              {block.type === 'text' ? (
                <div className="markdown-prose text-[13px] leading-relaxed">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeHighlight]}
                  >
                    {block.content}
                  </ReactMarkdown>
                </div>
              ) : (
                <ExecutableCodeBlock
                  code={block.content}
                  language={block.language || message.language || 'javascript'}
                  stepTitle={block.stepTitle}
                  sessionId={currentSession?.session_id || 'default'}
                  messageId={message.message_id}
                />
              )}
            </div>
          ))}
        </Card>
        <div className="text-[10px] text-muted-foreground/50 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {new Date(message.timestamp).toLocaleTimeString('zh-CN')}
        </div>
      </div>
    </div>
  );
}
