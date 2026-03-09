import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

export const chatApi = {
  sendMessage: (sessionId: string, message: string) =>
    api.post(`/chat/send`, { session_id: sessionId, message }),
  
  executeCode: (sessionId: string, messageId: string, code?: string) =>
    api.post(`/chat/execute`, { session_id: sessionId, message_id: messageId, code }),
  
  getSession: (sessionId: string) =>
    api.get(`/chat/sessions/${sessionId}`),
};

export const sandboxApi = {
  getSandboxes: () => api.get('/sandboxes'),
  
  getSandbox: (sandboxId: string) => api.get(`/sandboxes/${sandboxId}`),
  
  getLogs: (sandboxId: string, limit: number = 100) =>
    api.get(`/log/${sandboxId}`, { params: { limit } }),
};
