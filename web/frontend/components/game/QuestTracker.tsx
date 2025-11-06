/**
 * 任务追踪组件
 * 显示当前激活的任务、目标进度、任务完成动画
 */

'use client';

import { useEffect, useState } from 'react';
import { CheckCircle2, Circle, Trophy, Star, Clock, Scroll } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useGameStore } from '@/stores/gameStore';
import { Quest, QuestObjective } from '@/types/game';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface QuestTrackerProps {
  className?: string;
}

export function QuestTracker({ className }: QuestTrackerProps) {
  const { quests, setQuests } = useGameStore();
  const [completedQuests, setCompletedQuests] = useState<string[]>([]);

  // 加载任务列表
  useEffect(() => {
    loadQuests();
  }, []);

  const loadQuests = async () => {
    try {
      const response = await fetch('/api/game/quests');
      if (!response.ok) throw new Error('加载任务失败');

      const data = await response.json();
      setQuests(data.quests || []);
    } catch (error) {
      console.error('[QuestTracker] 加载任务失败:', error);
    }
  };

  // 监听任务完成
  useEffect(() => {
    const newCompleted = quests
      .filter((q) => q.status === 'completed')
      .map((q) => q.quest_id || q.id)
      .filter((id): id is string => id !== undefined && !completedQuests.includes(id));

    if (newCompleted.length > 0) {
      setCompletedQuests((prev) => [...prev, ...newCompleted]);

      // 3秒后移除完成动画
      setTimeout(() => {
        setCompletedQuests((prev) => prev.filter((id) => !newCompleted.includes(id)));
      }, 3000);
    }
  }, [quests]);

  // 按状态分类任务
  const activeQuests = quests.filter((q) => q.status === 'active');
  const availableQuests = quests.filter((q) => q.status === 'inactive');
  const completedQuestsData = quests.filter((q) => q.status === 'completed');

  // 计算任务进度
  const calculateProgress = (quest: Quest) => {
    if (!quest.objectives || quest.objectives.length === 0) return 0;

    const completed = quest.objectives.filter((obj) => obj.completed).length;
    return (completed / quest.objectives.length) * 100;
  };

  // 渲染任务目标
  const renderObjective = (objective: QuestObjective) => (
    <div
      key={objective.id}
      className={cn(
        'flex items-start gap-2 py-1 transition-opacity',
        objective.completed && 'opacity-50'
      )}
    >
      {objective.completed ? (
        <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
      ) : (
        <Circle className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
      )}
      <div className="flex-1 text-sm">
        <p className={cn(objective.completed && 'line-through text-muted-foreground')}>
          {objective.description}
        </p>
      </div>
    </div>
  );

  // 渲染单个任务
  const renderQuest = (quest: Quest, showProgress: boolean = true) => {
    const progress = calculateProgress(quest);
    const questId = quest.quest_id || quest.id;
    const isCompleting = completedQuests.includes(questId);

    const questTypeIcon = <Scroll className="w-4 h-4 text-blue-500" />;

    return (
      <motion.div
        key={questId}
        layout
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className={cn(
          'border rounded-lg p-4 space-y-3 transition-all',
          isCompleting && 'bg-green-500/10 border-green-500'
        )}
      >
        {/* 任务头部 */}
        <div className="flex items-start gap-2">
          {questTypeIcon}
          <div className="flex-1">
            <h3 className="font-semibold text-sm flex items-center gap-2">
              {quest.title}
              {isCompleting && (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="flex items-center gap-1 text-green-500 text-xs"
                >
                  <Trophy className="w-3 h-3" />
                  已完成!
                </motion.span>
              )}
            </h3>
            <p className="text-xs text-muted-foreground mt-1">{quest.description}</p>
          </div>
        </div>

        {/* 任务目标 */}
        {quest.objectives && quest.objectives.length > 0 && (
          <div className="space-y-1 pl-6">
            {quest.objectives.map(renderObjective)}
          </div>
        )}

        {/* 进度条 */}
        {showProgress && quest.objectives && quest.objectives.length > 0 && (
          <div className="space-y-1">
            <Progress value={progress} className="h-2" />
            <p className="text-xs text-muted-foreground text-right">
              {Math.round(progress)}% 完成
            </p>
          </div>
        )}

        {/* 奖励预览 */}
        {quest.rewards && (
          <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2 border-t">
            {quest.rewards.exp && (
              <div className="flex items-center gap-1">
                <Star className="w-3 h-3" />
                <span>{quest.rewards.exp} 经验</span>
              </div>
            )}
            {quest.rewards.money && (
              <div className="flex items-center gap-1">
                <Trophy className="w-3 h-3 text-yellow-500" />
                <span>{quest.rewards.money} 金币</span>
              </div>
            )}
          </div>
        )}
      </motion.div>
    );
  };

  return (
    <div className={cn('h-full bg-background border rounded-lg', className)}>
      <Tabs defaultValue="active" className="h-full flex flex-col">
        {/* 标签页 */}
        <TabsList className="w-full rounded-none border-b">
          <TabsTrigger value="active" className="flex-1">
            激活中 ({activeQuests.length})
          </TabsTrigger>
          <TabsTrigger value="available" className="flex-1">
            可接取 ({availableQuests.length})
          </TabsTrigger>
          <TabsTrigger value="completed" className="flex-1">
            已完成 ({completedQuestsData.length})
          </TabsTrigger>
        </TabsList>

        {/* 激活的任务 */}
        <TabsContent value="active" className="flex-1 mt-0">
          <ScrollArea className="h-full p-4">
            <AnimatePresence>
              {activeQuests.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  <Circle className="w-12 h-12 mb-2" />
                  <p className="text-sm">暂无激活的任务</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {activeQuests.map((quest) => renderQuest(quest))}
                </div>
              )}
            </AnimatePresence>
          </ScrollArea>
        </TabsContent>

        {/* 可接取的任务 */}
        <TabsContent value="available" className="flex-1 mt-0">
          <ScrollArea className="h-full p-4">
            {availableQuests.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <Star className="w-12 h-12 mb-2" />
                <p className="text-sm">暂无可接取的任务</p>
              </div>
            ) : (
              <div className="space-y-4">
                {availableQuests.map((quest) => renderQuest(quest, false))}
              </div>
            )}
          </ScrollArea>
        </TabsContent>

        {/* 已完成的任务 */}
        <TabsContent value="completed" className="flex-1 mt-0">
          <ScrollArea className="h-full p-4">
            {completedQuestsData.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <Trophy className="w-12 h-12 mb-2" />
                <p className="text-sm">还没有完成任务</p>
              </div>
            ) : (
              <div className="space-y-4">
                {completedQuestsData.map((quest) => renderQuest(quest, false))}
              </div>
            )}
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}
