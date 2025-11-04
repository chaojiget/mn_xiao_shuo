/**
 * 游戏主页面
 * 集成 DM 界面、任务追踪、NPC 对话、游戏状态面板
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Save, Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DmInterface } from '@/components/game/DmInterface';
import { QuestTracker } from '@/components/game/QuestTracker';
import { NpcDialog } from '@/components/game/NpcDialog';
import { GameStatePanel } from '@/components/game/GameStatePanel';
import { useGameStore } from '@/stores/gameStore';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

export default function GamePlayPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { gameState, setGameState, resetGame, setError } = useGameStore();
  const [sessionId, setSessionId] = useState<string>('');
  const [isInitializing, setIsInitializing] = useState(true);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  // 初始化游戏
  useEffect(() => {
    initGame();
  }, []);

  const initGame = async () => {
    try {
      setIsInitializing(true);

      const response = await fetch('/api/game/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          storyId: null, // 可以从 URL 参数获取
          playerConfig: null,
        }),
      });

      if (!response.ok) {
        throw new Error(`初始化失败: ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        setGameState(data.state);
        setSessionId(data.state.session_id);

        toast({
          title: '游戏开始',
          description: data.narration,
        });
      } else {
        throw new Error(data.error || '初始化失败');
      }
    } catch (error) {
      console.error('[GamePlay] 初始化失败:', error);
      setError(error instanceof Error ? error.message : '初始化失败');

      toast({
        title: '错误',
        description: '游戏初始化失败，请刷新页面重试',
        variant: 'destructive',
      });
    } finally {
      setIsInitializing(false);
    }
  };

  // 保存游戏
  const handleSaveGame = async () => {
    if (!gameState) return;

    try {
      const saveName = `存档 - 回合 ${gameState.turn_number}`;

      const response = await fetch('/api/game/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'default_user',
          slot_id: 1, // 默认槽位1，可以让用户选择
          save_name: saveName,
          game_state: gameState,
        }),
      });

      if (!response.ok) {
        throw new Error(`保存失败: ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        toast({
          title: '保存成功',
          description: `游戏已保存到槽位 ${data.slot_id}`,
        });
      } else {
        throw new Error(data.error || '保存失败');
      }
    } catch (error) {
      console.error('[GamePlay] 保存失败:', error);

      toast({
        title: '错误',
        description: '保存游戏失败',
        variant: 'destructive',
      });
    }
  };

  if (isInitializing) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-lg font-semibold">正在初始化游戏...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* 顶部工具栏 */}
      <header className="border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setShowMobileMenu(!showMobileMenu)}
          >
            {showMobileMenu ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </Button>
          <h1 className="text-xl font-bold">地下城主模式</h1>
        </div>

        <div className="flex items-center gap-2">
          {/* 保存按钮 */}
          <Button variant="outline" size="sm" onClick={handleSaveGame}>
            <Save className="w-4 h-4 mr-2" />
            保存游戏
          </Button>

          {/* 退出按钮 */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              if (confirm('确定要退出游戏吗？未保存的进度将丢失。')) {
                resetGame();
                router.push('/game');
              }
            }}
          >
            退出
          </Button>
        </div>
      </header>

      {/* 主内容区域 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧边栏 - 游戏状态（桌面端显示） */}
        <aside
          className={cn(
            'w-80 border-r overflow-y-auto',
            'hidden lg:block',
            showMobileMenu && 'absolute z-50 left-0 top-[57px] bottom-0 bg-background lg:relative lg:top-0'
          )}
        >
          <GameStatePanel className="h-full border-0" />
        </aside>

        {/* 中间主要内容 - DM 界面 */}
        <main className="flex-1 overflow-hidden">
          <DmInterface sessionId={sessionId} className="h-full border-0 rounded-none" />
        </main>

        {/* 右侧边栏 - 任务和 NPC（桌面端显示） */}
        <aside className="w-96 border-l hidden xl:flex flex-col overflow-hidden">
          {/* 任务追踪（上半部分） */}
          <div className="flex-1 min-h-0">
            <QuestTracker className="h-full border-0 border-b rounded-none" />
          </div>

          {/* NPC 对话（下半部分） */}
          <div className="flex-1 min-h-0">
            <NpcDialog className="h-full border-0 rounded-none" />
          </div>
        </aside>
      </div>

      {/* 移动端底部导航（平板和手机） */}
      <div className="lg:hidden border-t">
        <div className="grid grid-cols-3 gap-2 p-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              // 显示游戏状态弹窗
              toast({
                title: '游戏状态',
                description: `HP: ${gameState?.player?.hp || 100}/${gameState?.player?.maxHp || 100} | 位置: ${gameState?.world?.current_location || '未知'}`,
              });
            }}
          >
            状态
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              // 显示任务弹窗
              router.push('/game/quests');
            }}
          >
            任务
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              // 显示 NPC 弹窗
              router.push('/game/npcs');
            }}
          >
            NPC
          </Button>
        </div>
      </div>
    </div>
  );
}
