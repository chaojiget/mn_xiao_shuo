/**
 * 任务进度列表组件
 * 类似 Claude Artifacts 的工作进度展示
 */

'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, CheckCircle2, Circle, Loader2, File, Code, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  type?: 'file' | 'code' | 'text' | 'other';
  fileReference?: string; // 文件路径或引用
  progress?: number; // 0-100
  error?: string;
  timestamp?: number;
}

interface TaskProgressProps {
  tasks: Task[];
  title?: string;
  className?: string;
}

const typeIcons = {
  file: File,
  code: Code,
  text: FileText,
  other: Circle,
};

export function TaskProgress({ tasks, title = 'AI 工作进度', className }: TaskProgressProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const completedCount = tasks.filter((t) => t.status === 'completed').length;
  const totalCount = tasks.length;
  const progressPercentage = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  if (tasks.length === 0) {
    return null;
  }

  return (
    <div className={cn('border rounded-lg overflow-hidden bg-background', className)}>
      {/* 标题栏 */}
      <div
        className="flex items-center gap-2 px-4 py-2 bg-muted/50 border-b cursor-pointer hover:bg-muted transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="w-4 h-4 text-muted-foreground" />
        )}
        <span className="text-sm font-semibold">{title}</span>
        <Badge variant="secondary" className="ml-auto">
          {completedCount} / {totalCount}
        </Badge>
      </div>

      {/* 进度条 */}
      <div className="px-4 py-2 border-b">
        <Progress value={progressPercentage} className="h-1" />
      </div>

      {/* 任务列表 */}
      {isExpanded && (
        <div className="p-4 space-y-3">
          {tasks.map((task) => {
            const Icon = typeIcons[task.type || 'other'];

            return (
              <div
                key={task.id}
                className={cn(
                  'flex items-start gap-3 p-3 rounded-lg border transition-all',
                  task.status === 'in_progress' && 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800',
                  task.status === 'completed' && 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800',
                  task.status === 'error' && 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800',
                  task.status === 'pending' && 'bg-gray-50 dark:bg-gray-900/20 border-gray-200 dark:border-gray-800'
                )}
              >
                {/* 状态图标 */}
                <div className="flex-shrink-0 mt-0.5">
                  {task.status === 'in_progress' && (
                    <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                  )}
                  {task.status === 'completed' && (
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                  )}
                  {task.status === 'error' && (
                    <Circle className="w-4 h-4 text-red-500" />
                  )}
                  {task.status === 'pending' && (
                    <Circle className="w-4 h-4 text-gray-400" />
                  )}
                </div>

                {/* 任务内容 */}
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <Icon className="w-3 h-3 text-muted-foreground" />
                    <span className="text-sm font-medium">{task.title}</span>
                    {task.timestamp && (
                      <span className="text-xs text-muted-foreground ml-auto">
                        {new Date(task.timestamp).toLocaleTimeString()}
                      </span>
                    )}
                  </div>

                  {task.description && (
                    <p className="text-xs text-muted-foreground">{task.description}</p>
                  )}

                  {task.fileReference && (
                    <div className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 font-mono">
                      <File className="w-3 h-3" />
                      <span>{task.fileReference}</span>
                    </div>
                  )}

                  {task.error && (
                    <p className="text-xs text-red-600 dark:text-red-400">{task.error}</p>
                  )}

                  {task.progress !== undefined && task.status === 'in_progress' && (
                    <Progress value={task.progress} className="h-1 mt-2" />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
