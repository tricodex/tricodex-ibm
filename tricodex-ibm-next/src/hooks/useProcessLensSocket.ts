/**
 * ProcessLens WebSocket Hook
 */
import { useEffect, useRef, useState } from 'react';
import { AnalysisResult, ThoughtMessage } from '@/types';

interface ProcessLensSocketOptions {
  taskId: string | null;
  onUpdate?: (data: AnalysisResult) => void;
  onError?: (error: any) => void;
  autoReconnect?: boolean;
  maxRetries?: number;
}

interface SocketState {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  data: AnalysisResult | null;
  error?: any;
}

export const useProcessLensSocket = ({
  taskId,
  onUpdate,
  onError,
  autoReconnect = true,
  maxRetries = 5
}: ProcessLensSocketOptions) => {
  const [state, setState] = useState<SocketState>({ 
    status: 'disconnected', 
    data: null 
  });
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = () => {
    if (!taskId) return;

    try {
      const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws/${taskId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        setState(prev => ({ ...prev, status: 'connected' }));
        retriesRef.current = 0;
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'initial_state':
          case 'status_update':
            setState(prev => ({ ...prev, data: data.data }));
            onUpdate?.(data.data);
            break;
          case 'error':
            setState(prev => ({ ...prev, error: data.data }));
            onError?.(data.data);
            break;
          case 'pong':
            // Keep-alive response received
            break;
        }
      };

      ws.onerror = (error) => {
        setState(prev => ({ ...prev, status: 'error', error }));
        onError?.(error);
      };

      ws.onclose = () => {
        setState(prev => ({ ...prev, status: 'disconnected' }));
        wsRef.current = null;

        // Attempt reconnection if enabled
        if (autoReconnect && retriesRef.current < maxRetries) {
          const backoffDelay = Math.min(1000 * Math.pow(2, retriesRef.current), 10000);
          timeoutRef.current = setTimeout(() => {
            retriesRef.current++;
            connect();
          }, backoffDelay);
        }
      };

      // Setup ping interval
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);

      return () => clearInterval(pingInterval);
    } catch (error) {
      setState(prev => ({ ...prev, status: 'error', error }));
      onError?.(error);
    }
  };

  useEffect(() => {
    if (taskId) {
      connect();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [taskId]);

  return {
    status: state.status,
    data: state.data,
    error: state.error,
    isConnected: state.status === 'connected',
    thoughts: state.data?.thoughts || [],
    results: state.data?.results || null,
    latestThought: state.data?.thoughts?.[state.data.thoughts.length - 1],
    reconnect: () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      retriesRef.current = 0;
      connect();
    },
    requestUpdate: () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'status_request' }));
      }
    }
  };
};