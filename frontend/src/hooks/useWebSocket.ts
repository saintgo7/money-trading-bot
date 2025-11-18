import { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';

const SOCKET_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useWebSocket(userId: string) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const newSocket = io(SOCKET_URL, {
      query: { userId },
      transports: ['websocket'],
    });

    newSocket.on('connect', () => {
      console.log('WebSocket connected');
      setConnected(true);
    });

    newSocket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, [userId]);

  return { socket, connected };
}

export function useBotUpdates(botId: number, onUpdate: (data: any) => void) {
  const [socket, setSocket] = useState<Socket | null>(null);

  useEffect(() => {
    const newSocket = io(SOCKET_URL);

    newSocket.emit('subscribe_bot', { botId });

    newSocket.on('bot_update', (data) => {
      if (data.bot_id === botId) {
        onUpdate(data);
      }
    });

    setSocket(newSocket);

    return () => {
      newSocket.emit('unsubscribe_bot', { botId });
      newSocket.close();
    };
  }, [botId, onUpdate]);

  return socket;
}

export function usePriceUpdates(symbol: string, exchange: string, onUpdate: (data: any) => void) {
  const [socket, setSocket] = useState<Socket | null>(null);

  useEffect(() => {
    const newSocket = io(SOCKET_URL);

    newSocket.emit('subscribe_price', { symbol, exchange });

    newSocket.on('price_update', (data) => {
      if (data.symbol === symbol && data.exchange === exchange) {
        onUpdate(data);
      }
    });

    setSocket(newSocket);

    return () => {
      newSocket.emit('unsubscribe_price', { symbol, exchange });
      newSocket.close();
    };
  }, [symbol, exchange, onUpdate]);

  return socket;
}
