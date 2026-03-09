import axios from 'axios';

// 从环境变量读取 API 基础 URL，如果没有则使用默认值
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8181';

// 导出 WebSocket 基础 URL
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8181';

// API 客户端实例
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 代码执行 API
export const codeApi = {
  /**
   * 执行代码
   * @param sessionId 会话 ID
   * @param executeContextId 执行上下文 ID
   * @param code 要执行的代码
   * @param sandboxId 可选的沙箱 ID
   */
  execute: async (params: {
    session_id: string;
    execute_context_id: string;
    code: string;
    sandbox_id?: string;
  }) => {
    const response = await apiClient.post('/api/code/execute', params);
    return response.data;
  },

  /**
   * 获取执行结果
   * @param executeContextId 执行上下文 ID
   */
  getResult: async (executeContextId: string) => {
    const response = await apiClient.get(`/api/code/result/${executeContextId}`);
    return response.data;
  },
};

// 会话 API
export const sessionApi = {
  /**
   * 保存会话代码
   * @param sessionId 会话 ID
   * @param code 代码内容
   */
  saveCode: async (sessionId: string, code: string) => {
    const response = await apiClient.post(`/api/session/${sessionId}/code`, { code });
    return response.data;
  },

  /**
   * 获取会话代码
   * @param sessionId 会话 ID
   */
  getCode: async (sessionId: string) => {
    const response = await apiClient.get(`/api/session/${sessionId}/code`);
    return response.data;
  },

  /**
   * 获取会话执行历史
   * @param sessionId 会话 ID
   */
  getHistory: async (sessionId: string) => {
    const response = await apiClient.get(`/api/session/${sessionId}/history`);
    return response.data;
  },
};

// 沙箱 API
export const sandboxApi = {
  /**
   * 创建沙箱
   * @param sessionId 会话 ID
   */
  create: async (sessionId: string) => {
    const response = await apiClient.post('/api/sandbox/create', { session_id: sessionId });
    return response.data;
  },

  /**
   * 获取沙箱信息
   * @param sandboxId 沙箱 ID
   */
  get: async (sandboxId: string) => {
    const response = await apiClient.get(`/api/sandbox/${sandboxId}`);
    return response.data;
  },

  /**
   * 获取沙箱日志
   * @param sandboxId 沙箱 ID
   * @param executeContextId 可选的执行上下文 ID（用于过滤）
   */
  getLogs: async (sandboxId: string, executeContextId?: string) => {
    const params = executeContextId ? { execute_context_id: executeContextId } : {};
    const response = await apiClient.get(`/api/sandbox/${sandboxId}/logs`, { params });
    return response.data;
  },
};

export default apiClient;
