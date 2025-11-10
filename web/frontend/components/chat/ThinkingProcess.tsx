/**
 * 思考过程展示组件
 * 用于显示 AI 的推理过程（类似 Kimi K2 Thinking 的思考链）
 */

'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Brain, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

export interface ThinkingStep {
  id: string;
  title: string;
  content: string;
  status: 'thinking' | 'completed' | 'pending';
  timestamp?: number;
}

interface ThinkingProcessProps {
  steps: ThinkingStep[];
  isThinking?: boolean;
  className?: string;
}

export function ThinkingProcess({ steps, isThinking = false, className }: ThinkingProcessProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (steps.length === 0 && !isThinking) {
    return null;
  }

  return (
    <div className={cn('border rounded-lg overflow-hidden bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20', className)}>
      {/* 标题栏 */}
      <div
        className="flex items-center gap-2 px-4 py-2 bg-purple-100/50 dark:bg-purple-900/20 border-b cursor-pointer hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-purple-600 dark:text-purple-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-purple-600 dark:text-purple-400" />
        )}
        <Brain className="w-4 h-4 text-purple-600 dark:text-purple-400" />
        <span className="text-sm font-semibold text-purple-700 dark:text-purple-300">
          AI 思考过程
        </span>
        {isThinking && (
          <Loader2 className="w-3 h-3 text-purple-600 dark:text-purple-400 animate-spin ml-auto" />
        )}
        <Badge variant="secondary" className="ml-auto">
          {steps.length} 步
        </Badge>
      </div>

      {/* 思考步骤 */}
      {isExpanded && (
        <div className="p-4 space-y-3">
          {steps.map((step, index) => (
            <div
              key={step.id}
              className={cn(
                'flex items-start gap-3 p-3 rounded-lg transition-all',
                step.status === 'thinking' && 'bg-purple-100 dark:bg-purple-900/30 animate-pulse',
                step.status === 'completed' && 'bg-white dark:bg-gray-800/50',
                step.status === 'pending' && 'bg-gray-50 dark:bg-gray-900/30 opacity-60'
              )}
            >
              {/* 步骤编号 */}
              <div
                className={cn(
                  'flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold',
                  step.status === 'thinking' && 'bg-purple-500 text-white',
                  step.status === 'completed' && 'bg-green-500 text-white',
                  step.status === 'pending' && 'bg-gray-300 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                )}
              >
                {step.status === 'thinking' ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  index + 1
                )}
              </div>

              {/* 步骤内容 */}
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-foreground">
                    {step.title}
                  </span>
                  {step.timestamp && step.status === 'completed' && (
                    <span className="text-xs text-muted-foreground">
                      {new Date(step.timestamp).toLocaleTimeString()}
                    </span>
                  )}
                </div>
                {step.content && (
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                    {step.content}
                  </p>
                )}
              </div>
            </div>
          ))}

          {/* 正在思考指示器 */}
          {isThinking && steps.length === 0 && (
            <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">AI 正在思考...</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
