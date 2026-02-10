// Hook para conexao WebSocket com o chat
import { useEffect, useRef, useCallback } from 'react';
import { useStore } from '../store/useStore';
import type { Message } from '../types';

interface ChatResponse {
  type: string;
  session_id: string;
  message: string;
  metadata?: Record<string, unknown>;
  cart?: {
    items: Array<{
      book_id: string;
      title: string;
      quantity: number;
      price: number;
    }>;
    total: number;
  };
  search_results?: Array<{
    id: string;
    title: string;
    author: string;
    price: number;
    price_formatted: string;
    category: string;
  }>;
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number>();

  const {
    addMessage,
    setSessionId,
    setConnected,
    isConnected,
    triggerRefresh,
  } = useStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data: ChatResponse = JSON.parse(event.data);

          if (data.type === 'connected') {
            setSessionId(data.session_id);
            return;
          }

          if (data.type === 'response') {
            const message: Message = {
              id: crypto.randomUUID(),
              role: 'assistant',
              content: data.message,
              timestamp: new Date(),
              metadata: data.metadata,
            };
            addMessage(message);
            
            // Verificar se foi um checkout/compra concluida para atualizar estoque
            const isCheckout = 
              data.metadata?.checkout_completed || 
              data.metadata?.checkout_session_id ||
              data.message?.toLowerCase().includes('checkout criado') ||
              data.message?.toLowerCase().includes('compra realizada') ||
              data.message?.toLowerCase().includes('pedido confirmado');
            
            if (isCheckout) {
              // Aguardar um pouco para o banco atualizar e então refresh
              setTimeout(() => triggerRefresh(), 500);
            }
          }
        } catch (err) {
          console.error('Failed to parse message:', err);
        }
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);

        // Reconectar apos 3s
        reconnectTimeoutRef.current = window.setTimeout(() => {
          connect();
        }, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (err) {
      console.error('Failed to connect:', err);
    }
  }, [addMessage, setSessionId, setConnected, triggerRefresh]);

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    // Adicionar mensagem do usuario localmente
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    addMessage(userMessage);

    // Enviar para o servidor
    wsRef.current.send(JSON.stringify({ message: content }));
  }, [addMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    wsRef.current?.close();
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    sendMessage,
    isConnected,
    reconnect: connect,
  };
}
