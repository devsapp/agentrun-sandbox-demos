// 代码执行语言类型
export type CodeLanguage = 'javascript' | 'shell' | 'python';

export interface Message {
  message_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  code?: string;
  language?: CodeLanguage;  // 代码语言类型
  timestamp: number;
}

export interface ChatSession {
  session_id: string;
  messages: Message[];
  sandbox_id?: string;
  base_url?: string;  // Sandbox 基础 URL
  execute_context_id?: string;  // 执行上下文ID
  cdp_url?: string;
  vnc_url?: string;
  code?: string;  // 当前会话的代码
  language?: CodeLanguage;  // 当前会话的代码语言
  created_at: number;
  last_activity: number;
}

export interface Sandbox {
  sandbox_id: string;
  base_url?: string;  // Sandbox 基础 URL，如 wss://xxx.aliyuncs.com/sandboxes/01KFZ9YQ18R9KR9ZS6W3NXNV1A
  cdp_url?: string;
  vnc_url?: string;
  last_access_at: number;
  log_count: number;
}

export interface LogEntry {
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  message: string;
  timestamp: number;
  extra?: Record<string, any>;
}
