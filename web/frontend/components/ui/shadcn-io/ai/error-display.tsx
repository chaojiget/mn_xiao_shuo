/**
 * Error Display component with retry functionality
 * For AI chat error handling
 */

'use client';

import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { HTMLAttributes } from 'react';

export type ErrorDisplayProps = HTMLAttributes<HTMLDivElement> & {
  error: string | Error;
  onRetry?: () => void;
  retryText?: string;
};

export const ErrorDisplay = ({
  error,
  onRetry,
  retryText = '重试',
  className,
  ...props
}: ErrorDisplayProps) => {
  const errorMessage = typeof error === 'string' ? error : error.message;

  return (
    <Alert variant="destructive" className={cn('my-4', className)} {...props}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>发生错误</AlertTitle>
      <AlertDescription className="mt-2 flex flex-col gap-2">
        <p className="text-sm">{errorMessage}</p>
        {onRetry && (
          <Button
            onClick={onRetry}
            variant="outline"
            size="sm"
            className="self-start"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            {retryText}
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
};
