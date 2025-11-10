/**
 * AI 建议芯片组件
 * 类似 ChatGPT 的后续提示建议，引导用户继续对话
 */

'use client';

import { useState } from 'react';
import { Sparkles, ArrowRight, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

export interface Suggestion {
  id: string;
  text: string;
  category?: 'explore' | 'action' | 'question' | 'creative';
  icon?: string;
}

interface SuggestionChipsProps {
  suggestions: Suggestion[];
  onSelect: (suggestion: Suggestion) => void;
  onRefresh?: () => void;
  isLoading?: boolean;
  className?: string;
}

const categoryConfig = {
  explore: {
    color: 'bg-blue-500/10 hover:bg-blue-500/20 border-blue-500/30 text-blue-700 dark:text-blue-300',
    icon: '🗺️',
  },
  action: {
    color: 'bg-red-500/10 hover:bg-red-500/20 border-red-500/30 text-red-700 dark:text-red-300',
    icon: '⚔️',
  },
  question: {
    color: 'bg-purple-500/10 hover:bg-purple-500/20 border-purple-500/30 text-purple-700 dark:text-purple-300',
    icon: '❓',
  },
  creative: {
    color: 'bg-green-500/10 hover:bg-green-500/20 border-green-500/30 text-green-700 dark:text-green-300',
    icon: '✨',
  },
};

export function SuggestionChips({
  suggestions,
  onSelect,
  onRefresh,
  isLoading = false,
  className,
}: SuggestionChipsProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (suggestions.length === 0 && !isLoading) {
    return null;
  }

  return (
    <div className={cn('border rounded-lg overflow-hidden bg-background', className)}>
      {/* 标题栏 */}
      <div className="flex items-center gap-2 px-4 py-2 bg-muted/50 border-b">
        <Sparkles className="w-4 h-4 text-yellow-500" />
        <span className="text-sm font-semibold">AI 建议</span>
        {onRefresh && (
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto h-6 px-2"
            onClick={onRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={cn('w-3 h-3', isLoading && 'animate-spin')} />
          </Button>
        )}
      </div>

      {/* 建议列表 */}
      {isExpanded && (
        <ScrollArea className="w-full">
          <div className="p-3 flex flex-wrap gap-2">
            {suggestions.map((suggestion) => {
              const category = suggestion.category || 'explore';
              const config = categoryConfig[category];

              return (
                <button
                  key={suggestion.id}
                  onClick={() => onSelect(suggestion)}
                  disabled={isLoading}
                  className={cn(
                    'inline-flex items-center gap-2 px-3 py-2 rounded-full border text-sm font-medium transition-all',
                    'hover:scale-105 active:scale-95',
                    'disabled:opacity-50 disabled:cursor-not-allowed',
                    config.color
                  )}
                >
                  <span className="text-base">{suggestion.icon || config.icon}</span>
                  <span>{suggestion.text}</span>
                  <ArrowRight className="w-3 h-3 opacity-50" />
                </button>
              );
            })}

            {/* 加载状态 */}
            {isLoading && (
              <div className="inline-flex items-center gap-2 px-3 py-2 rounded-full border bg-muted/50 text-sm">
                <RefreshCw className="w-3 h-3 animate-spin" />
                <span className="text-muted-foreground">生成建议中...</span>
              </div>
            )}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
