/**
 * LocalStorage 工具函数
 * 用于持久化全局单会话数据
 */

import type { CodeLanguage } from '@/types';

const STORAGE_KEYS = {
  CURRENT_SANDBOX: 'agentrun_current_sandbox',
  CURRENT_SESSION: 'agentrun_current_session',
} as const;

export interface StoredSandbox {
  sandbox_id: string;
  base_url?: string;
  cdp_url?: string;
  vnc_url?: string;
  last_access_at: number;
  log_count: number;
}

export interface StoredMessage {
  message_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  code?: string;
  language?: CodeLanguage;
  timestamp: number;
}

export interface StoredChatSession {
  session_id: string;
  messages: StoredMessage[];
  sandbox_id?: string;
  base_url?: string;  // Sandbox 基础 URL
  execute_context_id?: string;
  cdp_url?: string;
  vnc_url?: string;
  code?: string;
  language?: CodeLanguage;
  created_at: number;
  last_activity: number;
}

/**
 * 保存当前 sandbox 到 localStorage
 */
export function saveCurrentSandbox(sandbox: StoredSandbox | null): void {
  try {
    if (sandbox) {
      localStorage.setItem(STORAGE_KEYS.CURRENT_SANDBOX, JSON.stringify(sandbox));
    } else {
      localStorage.removeItem(STORAGE_KEYS.CURRENT_SANDBOX);
    }
  } catch (error) {
    console.error('Failed to save current sandbox to localStorage:', error);
  }
}

/**
 * 从 localStorage 加载当前 sandbox
 */
export function loadCurrentSandbox(): StoredSandbox | null {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.CURRENT_SANDBOX);
    if (!data) return null;
    
    const sandbox = JSON.parse(data) as StoredSandbox;
    
    // 检查是否过期（超过 7 天未访问）
    const sevenDaysAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
    if (sandbox.last_access_at < sevenDaysAgo) {
      // 过期，清除
      saveCurrentSandbox(null);
      return null;
    }
    
    return sandbox;
  } catch (error) {
    console.error('Failed to load current sandbox from localStorage:', error);
    return null;
  }
}

/**
 * 保存当前会话到 localStorage
 */
export function saveCurrentSession(session: StoredChatSession | null): void {
  try {
    if (session) {
      localStorage.setItem(STORAGE_KEYS.CURRENT_SESSION, JSON.stringify(session));
    } else {
      localStorage.removeItem(STORAGE_KEYS.CURRENT_SESSION);
    }
  } catch (error) {
    console.error('Failed to save current session to localStorage:', error);
  }
}

/**
 * 从 localStorage 加载当前会话
 */
export function loadCurrentSession(): StoredChatSession | null {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.CURRENT_SESSION);
    if (!data) return null;
    
    const session = JSON.parse(data) as StoredChatSession;
    
    // 检查是否过期（超过 30 天未活动）
    const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000;
    if (session.last_activity < thirtyDaysAgo) {
      // 过期，清除
      saveCurrentSession(null);
      return null;
    }
    
    return session;
  } catch (error) {
    console.error('Failed to load current session from localStorage:', error);
    return null;
  }
}

/**
 * 清除所有持久化数据
 */
export function clearStorage(): void {
  try {
    localStorage.removeItem(STORAGE_KEYS.CURRENT_SANDBOX);
    localStorage.removeItem(STORAGE_KEYS.CURRENT_SESSION);
  } catch (error) {
    console.error('Failed to clear localStorage:', error);
  }
}
