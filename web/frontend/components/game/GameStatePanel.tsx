/**
 * 游戏状态面板组件
 * 显示 HP/资源/背包/位置信息
 */

'use client';

import { useState } from 'react';
import { Heart, Coins, Zap, MapPin, Package, ChevronRight } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useGameStore } from '@/stores/gameStore';
import { InventoryItem } from '@/types/game';
import { cn } from '@/lib/utils';

interface GameStatePanelProps {
  className?: string;
  compact?: boolean; // 紧凑模式（适用于侧边栏）
}

export function GameStatePanel({ className, compact = false }: GameStatePanelProps) {
  const { gameState } = useGameStore();
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);

  if (!gameState) {
    return (
      <div className={cn('h-full bg-background border rounded-lg flex items-center justify-center', className)}>
        <p className="text-sm text-muted-foreground">游戏未初始化</p>
      </div>
    );
  }

  const hpPercent = (gameState.player.hp / gameState.player.maxHp) * 100;

  // 渲染物品卡片
  const renderItem = (item: InventoryItem) => {
    const typeColors: Record<string, string> = {
      weapon: 'text-red-500',
      armor: 'text-blue-500',
      consumable: 'text-green-500',
      quest_item: 'text-purple-500',
      misc: 'text-gray-500',
    };

    const typeLabels: Record<string, string> = {
      weapon: '武器',
      armor: '防具',
      consumable: '消耗品',
      quest_item: '任务物品',
      misc: '杂物',
    };

    return (
      <div
        key={item.id}
        className={cn(
          'border rounded-lg p-3 cursor-pointer transition-all hover:bg-accent',
          selectedItem?.id === item.id && 'bg-accent border-primary'
        )}
        onClick={() => setSelectedItem(item)}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h4 className="font-semibold text-sm">{item.name}</h4>
              {item.quantity > 1 && (
                <span className="text-xs text-muted-foreground">x{item.quantity}</span>
              )}
            </div>
            <p className={cn('text-xs font-medium mt-1', typeColors[item.type])}>
              {typeLabels[item.type]}
            </p>
            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
              {item.description}
            </p>
          </div>
          <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        </div>
      </div>
    );
  };

  // 紧凑模式渲染
  if (compact) {
    return (
      <div className={cn('bg-background border rounded-lg p-4 space-y-4', className)}>
        {/* HP */}
        <div>
          <div className="flex items-center justify-between text-sm mb-2">
            <div className="flex items-center gap-2 text-red-500">
              <Heart className="w-4 h-4" />
              <span>生命值</span>
            </div>
            <span className="font-semibold">
              {gameState.player.hp} / {gameState.player.maxHp}
            </span>
          </div>
          <Progress value={hpPercent} className="h-2" />
        </div>

        {/* 资源 */}
        <div className="grid grid-cols-2 gap-2">
          {gameState.player.money !== undefined && (
            <div className="flex items-center gap-2 text-sm">
              <Coins className="w-4 h-4 text-yellow-500" />
              <span>{gameState.player.money}</span>
            </div>
          )}
        </div>

        {/* 位置 */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <MapPin className="w-4 h-4" />
          <span>{gameState.map.currentNodeId}</span>
        </div>

        {/* 回合数 */}
        <div className="text-xs text-muted-foreground text-center pt-2 border-t">
          回合 {gameState.world.time}
        </div>
      </div>
    );
  }

  // 完整模式渲染
  return (
    <div className={cn('h-full bg-background border rounded-lg', className)}>
      <Tabs defaultValue="stats" className="h-full flex flex-col">
        {/* 标签页 */}
        <TabsList className="w-full rounded-none border-b">
          <TabsTrigger value="stats" className="flex-1">
            状态
          </TabsTrigger>
          <TabsTrigger value="inventory" className="flex-1">
            背包 ({gameState.player.inventory.length})
          </TabsTrigger>
        </TabsList>

        {/* 状态页 */}
        <TabsContent value="stats" className="flex-1 mt-0 p-4 space-y-4">
          {/* HP */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 text-red-500">
                <Heart className="w-5 h-5" />
                <span className="font-semibold">生命值</span>
              </div>
              <span className="font-bold text-lg">
                {gameState.player.hp} / {gameState.player.maxHp}
              </span>
            </div>
            <Progress value={hpPercent} className="h-3" />
          </div>

          {/* 资源 */}
          <div className="grid grid-cols-2 gap-4">
            {gameState.player.money !== undefined && (
              <div className="border rounded-lg p-3">
                <div className="flex items-center gap-2 text-yellow-500 mb-2">
                  <Coins className="w-5 h-5" />
                  <span className="text-sm font-semibold">金币</span>
                </div>
                <p className="text-2xl font-bold">{gameState.player.money}</p>
              </div>
            )}
          </div>

          {/* 位置信息 */}
          <div className="border rounded-lg p-3">
            <div className="flex items-center gap-2 text-green-500 mb-2">
              <MapPin className="w-5 h-5" />
              <span className="text-sm font-semibold">当前位置</span>
            </div>
            <p className="text-lg font-medium">{gameState.player.location}</p>
          </div>

          {/* 游戏信息 */}
          <div className="border rounded-lg p-3 text-sm space-y-1">
            <div className="flex justify-between">
              <span className="text-muted-foreground">回合数</span>
              <span className="font-semibold">{gameState.world.time}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">任务数</span>
              <span className="font-semibold">{gameState.quests.length}</span>
            </div>
          </div>
        </TabsContent>

        {/* 背包页 */}
        <TabsContent value="inventory" className="flex-1 mt-0">
          <ScrollArea className="h-full p-4">
            {gameState.player.inventory.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <Package className="w-12 h-12 mb-2" />
                <p className="text-sm">背包是空的</p>
              </div>
            ) : (
              <div className="space-y-3">
                {gameState.player.inventory.map(renderItem)}
              </div>
            )}
          </ScrollArea>

          {/* 选中物品详情 */}
          {selectedItem && (
            <div className="border-t p-4 bg-accent/50">
              <h3 className="font-semibold mb-2">{selectedItem.name}</h3>
              <p className="text-sm text-muted-foreground mb-3">
                {selectedItem.description}
              </p>
              {selectedItem.effects && Object.keys(selectedItem.effects).length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-muted-foreground">效果:</p>
                  {Object.entries(selectedItem.effects).map(([key, value]) => (
                    <p key={key} className="text-xs">
                      <span className="text-muted-foreground capitalize">{key}:</span>{' '}
                      <span className="font-semibold">{String(value)}</span>
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
