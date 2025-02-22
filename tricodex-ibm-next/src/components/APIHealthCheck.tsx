import React, { useEffect, useState } from 'react';
import { checkHealth } from '@/lib/api';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { CheckCircle2, XCircle } from 'lucide-react';

export const APIHealthCheck = () => {
  const [status, setStatus] = useState<'checking' | 'healthy' | 'error'>('checking');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkAPIHealth = async () => {
      try {
        await checkHealth();
        setStatus('healthy');
      } catch (err) {
        setStatus('error');
        setError(err instanceof Error ? err.message : 'Failed to connect to API');
      }
    };

    checkAPIHealth();
  }, []);

  if (status === 'checking') return null;

  return (
    <Alert variant={status === 'healthy' ? 'default' : 'destructive'}>
      {status === 'healthy' ? (
        <CheckCircle2 className="h-4 w-4" />
      ) : (
        <XCircle className="h-4 w-4" />
      )}
      <AlertTitle>
        {status === 'healthy' ? 'API Connected' : 'API Connection Error'}
      </AlertTitle>
      <AlertDescription>
        {status === 'healthy'
          ? 'Successfully connected to the ProcessLens API'
          : `Failed to connect to API: ${error}`}
      </AlertDescription>
    </Alert>
  );
};

export default APIHealthCheck;