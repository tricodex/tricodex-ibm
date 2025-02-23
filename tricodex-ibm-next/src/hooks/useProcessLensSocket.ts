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
  const [state, setState] = useState<SocketState>({ status: 'disconnected', data: null });
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = () => {
    if (!taskId) return;

    try {
      const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws/${taskId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.debug('WebSocket connection opened for task:', taskId);
        setState(prev => ({ ...prev, status: 'connected' }));
        retriesRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          // Pre-validate raw message
          if (!event.data) {
            throw new Error('Empty message received');
          }

          // Parse and validate message structure
          const parsed = JSON.parse(event.data);
          if (!parsed || typeof parsed !== 'object') {
            throw new Error('Invalid message format');
          }

          // Ensure required fields exist
          const { type, data } = parsed;
          if (!type || !data) {
            throw new Error('Missing required message fields');
          }

          // Process message based on type
          switch (type) {
            case 'initial_state':
            case 'status_update':
              // Transform timestamps
              const transformedData = {
                ...data,
                thoughts: (data.thoughts || []).map((thought: any) => ({
                  ...thought,
                  timestamp: thought.timestamp ? new Date(thought.timestamp) : new Date()
                })),
                created_at: data.created_at ? new Date(data.created_at) : undefined,
                completed_at: data.completed_at ? new Date(data.completed_at) : undefined
              };

              console.debug(`Received ${type}:`, transformedData);
              setState(prev => ({ ...prev, data: transformedData }));
              onUpdate?.(transformedData);
              break;

            case 'error':
              console.error('Server error:', data);
              setState(prev => ({ ...prev, error: data }));
              onError?.(data);
              break;

            case 'pong':
              console.debug('Server heartbeat received');
              break;

            default:
              console.warn('Unknown message type:', type);
          }
        } catch (e) {
          const error = `WebSocket message handling error: ${e instanceof Error ? e.message : 'Unknown error'}`;
          console.error(error, '\nRaw message:', event.data);
          onError?.(error);
        }
      };

      ws.onerror = (error) => {
        const errorMsg = 'WebSocket error occurred';
        console.error(errorMsg, error);
        setState(prev => ({ 
          ...prev, 
          status: 'error',
          error: errorMsg
        }));
        onError?.(error);
      };

      ws.onclose = () => {
        console.debug('WebSocket connection closed');
        setState(prev => ({ ...prev, status: 'disconnected' }));
        wsRef.current = null;

        if (autoReconnect && retriesRef.current < maxRetries) {
          const backoffDelay = Math.min(1000 * Math.pow(2, retriesRef.current), 10000);
          console.debug(`Scheduling reconnection in ${backoffDelay}ms (attempt ${retriesRef.current + 1}/${maxRetries})`);
          
          timeoutRef.current = setTimeout(() => {
            retriesRef.current++;
            connect();
          }, backoffDelay);
        }
      };

      // Setup heartbeat
      const heartbeatInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);

      return () => clearInterval(heartbeatInterval);

    } catch (error) {
      console.error('WebSocket connection error:', error);
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