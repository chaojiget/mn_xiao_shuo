/**
 * Response component for AI-generated text with Markdown support
 * Simplified version adapted from shadcn/ui AI Elements
 */

'use client';

import { cn } from '@/lib/utils';
import type { HTMLAttributes } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';

export type ResponseProps = HTMLAttributes<HTMLDivElement> & {
  children: string;
};

export const Response = ({ className, children, ...props }: ResponseProps) => {
  return (
    <div
      className={cn(
        'size-full prose prose-sm dark:prose-invert max-w-none',
        '[&>*:first-child]:mt-0 [&>*:last-child]:mb-0',
        className
      )}
      {...props}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '');
            const inline = !match;
            return !inline && match ? (
              <SyntaxHighlighter
                style={oneDark}
                language={match[1]}
                PreTag="div"
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className={cn('rounded bg-muted px-1.5 py-0.5', className)} {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
};
