// hooks/useAnalysisSocket.ts
import { useEffect, useState, useCallback, useRef } from 'react';

interface ThoughtMessage {
  timestamp: string;
  stage: string;
  thought: string;
  progress: number;
}

interface AnalysisUpdate {
  type: 'thought_update' | 'analysis_complete' | 'analysis_error' | 'pong';
  data: any;
}

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
const RETRY_INTERVALS = [1000, 2000, 3000, 5000, 8000]; // Progressive retry intervals
const PING_INTERVAL = 30000; // 30 seconds

export function useAnalysisSocket(taskId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);
  const lastPongRef = useRef<number>(Date.now());
  
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [thoughts, setThoughts] = useState<ThoughtMessage[]>([]);
  const [results, setResults] = useState<any | null>(null);

  const cleanup = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const startPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }
    
    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
        
        // Check if we haven't received a pong in twice the ping interval
        if (Date.now() - lastPongRef.current > PING_INTERVAL * 2) {
          console.warn('No pong received, reconnecting...');
          cleanup();
          connect(); // Trigger reconnection
        }
      }
    }, PING_INTERVAL);
  }, [cleanup]);

  const connect = useCallback(() => {
    if (!taskId || wsRef.current) return;

    try {
      const ws = new WebSocket(`${WS_BASE_URL}/ws/${taskId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        startPingInterval();
        retryCountRef.current = 0; // Reset retry count on successful connection
      };

      ws.onmessage = (event) => {
        try {
          const update: AnalysisUpdate = JSON.parse(event.data);
          
          switch (update.type) {
            case 'thought_update':
              setThoughts(prev => [...prev, update.data]);
              break;
            case 'analysis_complete':
              setResults(update.data.results);
              setIsConnected(false);
              cleanup();
              break;
            case 'analysis_error':
              setError(update.data.error);
              setIsConnected(false);
              cleanup();
              break;
            case 'pong':
              lastPongRef.current = Date.now();
              break;
            default:
              console.warn('Unknown message type:', update.type);
          }
        } catch (e) {
          console.error('Error parsing message:', e);
        }
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        cleanup();
        
        // Only attempt reconnection if analysis isn't complete and we haven't hit max retries
        if (!results && !error && retryCountRef.current < RETRY_INTERVALS.length) {
          const delay = RETRY_INTERVALS[retryCountRef.current];
          console.log(`Connection closed. Retrying in ${delay}ms...`);
          
          retryTimeoutRef.current = setTimeout(() => {
            retryCountRef.current++;
            connect();
          }, delay);
        }
      };

      ws.onerror = () => {
        console.error('WebSocket error occurred');
        setError('Connection error occurred');
      };

    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError('Failed to establish connection');
    }
  }, [taskId, startPingInterval, cleanup]);

  useEffect(() => {
    connect();
    return cleanup;
  }, [connect, cleanup]);

  return {
    isConnected,
    error,
    thoughts,
    results,
    latestThought: thoughts[thoughts.length - 1]
  };
}