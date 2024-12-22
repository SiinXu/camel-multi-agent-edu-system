import { useState, useEffect } from 'react';

export function useWebSocket(url) {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setSocket(ws);
      setConnected(true);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setSocket(null);
      setConnected(false);
    };

    return () => {
      if (ws) ws.close();
    };
  }, [url]);

  return { socket, connected };
}
