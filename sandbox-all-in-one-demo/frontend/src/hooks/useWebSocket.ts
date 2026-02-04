import { useEffect, useRef, useState } from 'react';

interface UseWebSocketOptions {
  onMessage?: (data: any) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
}

export function useWebSocket(url: string | null, options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  
  useEffect(() => {
    if (!url) return;
    
    const ws = new WebSocket(url);
    wsRef.current = ws;
    
    ws.onopen = () => {
      setIsConnected(true);
      options.onOpen?.();
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      options.onMessage?.(data);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      options.onClose?.();
    };
    
    ws.onerror = (error) => {
      options.onError?.(error);
    };
    
    return () => {
      ws.close();
    };
  }, [url]);
  
  const send = (data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  };
  
  return { isConnected, send };
}
