/**
 * NPC 对话组件
 * 显示 NPC 头像、关系指示器、对话历史
 */

'use client';

import { useState, useEffect } from 'react';
import { Heart, Shield, MessageCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import { useGameStore } from '@/stores/gameStore';
import { NPC, NPCRelationship } from '@/types/game';
import { cn } from '@/lib/utils';

interface NpcDialogProps {
  className?: string;
}

export function NpcDialog({ className }: NpcDialogProps) {
  const { activeNpc, setActiveNpc, npcs, setNpcs } = useGameStore();
  const [localNpcs, setLocalNpcs] = useState<NPC[]>([]);

  // 加载当前位置的 NPC
  useEffect(() => {
    loadNpcs();
  }, []);

  const loadNpcs = async () => {
    try {
      const response = await fetch('/api/game/npcs?status=active');
      if (!response.ok) throw new Error('加载 NPC 失败');

      const data = await response.json();
      setNpcs(data.npcs || []);
      setLocalNpcs(data.npcs || []);
    } catch (error) {
      console.error('[NpcDialog] 加载 NPC 失败:', error);
    }
  };

  // 获取关系等级文本和颜色
  const getRelationshipInfo = (relationship?: NPCRelationship) => {
    if (!relationship) return { text: '陌生人', color: 'text-gray-500' };

    const { relationship_type, affinity } = relationship;

    const typeMap: Record<string, { text: string; color: string }> = {
      stranger: { text: '陌生人', color: 'text-gray-500' },
      acquaintance: { text: '熟人', color: 'text-blue-500' },
      friend: { text: '朋友', color: 'text-green-500' },
      ally: { text: '盟友', color: 'text-purple-500' },
      enemy: { text: '敌人', color: 'text-red-500' },
    };

    return typeMap[relationship_type] || typeMap.stranger;
  };

  // 渲染 NPC 卡片
  const renderNpcCard = (npc: NPC) => {
    const relationshipInfo = getRelationshipInfo(npc.relationship);

    return (
      <div
        key={npc.npc_id}
        className={cn(
          'border rounded-lg p-4 cursor-pointer transition-all hover:bg-accent',
          activeNpc?.npc_id === npc.npc_id && 'bg-accent border-primary'
        )}
        onClick={() => setActiveNpc(npc)}
      >
        {/* NPC 头像和名称 */}
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-lg">
            {npc.name.charAt(0)}
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-sm">{npc.name}</h3>
            <p className="text-xs text-muted-foreground">{npc.role}</p>
            <p className={cn('text-xs font-medium mt-1', relationshipInfo.color)}>
              {relationshipInfo.text}
            </p>
          </div>
        </div>

        {/* 关系指标 */}
        {npc.relationship && (
          <div className="mt-3 space-y-2">
            {/* 好感度 */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-1 text-pink-500">
                  <Heart className="w-3 h-3" />
                  <span>好感度</span>
                </div>
                <span className="text-muted-foreground">
                  {npc.relationship.affinity > 0 ? '+' : ''}
                  {npc.relationship.affinity}
                </span>
              </div>
              <Progress
                value={((npc.relationship.affinity + 100) / 200) * 100}
                className="h-1"
              />
            </div>

            {/* 信任度 */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-1 text-blue-500">
                  <Shield className="w-3 h-3" />
                  <span>信任度</span>
                </div>
                <span className="text-muted-foreground">{npc.relationship.trust}</span>
              </div>
              <Progress value={npc.relationship.trust} className="h-1" />
            </div>
          </div>
        )}

        {/* NPC 特质 */}
        {npc.personality_traits && npc.personality_traits.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {npc.personality_traits.slice(0, 3).map((trait, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 bg-secondary rounded text-xs text-muted-foreground"
              >
                {trait}
              </span>
            ))}
          </div>
        )}
      </div>
    );
  };

  // 渲染对话详情
  const renderNpcDetails = (npc: NPC) => {
    const relationshipInfo = getRelationshipInfo(npc.relationship);

    return (
      <div className="h-full flex flex-col">
        {/* 头部 */}
        <div className="border-b p-4">
          <div className="flex items-start gap-3">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-2xl">
              {npc.name.charAt(0)}
            </div>
            <div className="flex-1">
              <h2 className="font-bold text-lg">{npc.name}</h2>
              <p className="text-sm text-muted-foreground">{npc.role}</p>
              <p className={cn('text-sm font-medium mt-1', relationshipInfo.color)}>
                {relationshipInfo.text}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setActiveNpc(null)}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* NPC 信息 */}
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {/* 描述 */}
            {npc.description && (
              <div>
                <h3 className="text-sm font-semibold mb-2">描述</h3>
                <p className="text-sm text-muted-foreground">{npc.description}</p>
              </div>
            )}

            {/* 性格特质 */}
            {npc.personality_traits && npc.personality_traits.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2">性格特质</h3>
                <div className="flex flex-wrap gap-2">
                  {npc.personality_traits.map((trait, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-secondary rounded-full text-sm"
                    >
                      {trait}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 说话风格 */}
            {npc.speech_style && (
              <div>
                <h3 className="text-sm font-semibold mb-2">说话风格</h3>
                <p className="text-sm text-muted-foreground italic">
                  "{npc.speech_style}"
                </p>
              </div>
            )}

            {/* 目标 */}
            {npc.goals && npc.goals.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2">目标</h3>
                <ul className="space-y-1">
                  {npc.goals.map((goal, idx) => (
                    <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="text-primary">•</span>
                      <span>{goal}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* 关系详情 */}
            {npc.relationship && (
              <div>
                <h3 className="text-sm font-semibold mb-2">关系详情</h3>
                <div className="space-y-3">
                  {/* 好感度 */}
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <div className="flex items-center gap-2 text-pink-500">
                        <Heart className="w-4 h-4" />
                        <span>好感度</span>
                      </div>
                      <span className="font-semibold">
                        {npc.relationship.affinity > 0 ? '+' : ''}
                        {npc.relationship.affinity}
                      </span>
                    </div>
                    <Progress
                      value={((npc.relationship.affinity + 100) / 200) * 100}
                      className="h-2"
                    />
                  </div>

                  {/* 信任度 */}
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <div className="flex items-center gap-2 text-blue-500">
                        <Shield className="w-4 h-4" />
                        <span>信任度</span>
                      </div>
                      <span className="font-semibold">{npc.relationship.trust}</span>
                    </div>
                    <Progress value={npc.relationship.trust} className="h-2" />
                  </div>
                </div>
              </div>
            )}

            {/* 记忆 */}
            {npc.memories && npc.memories.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2">记忆</h3>
                <div className="space-y-2">
                  {npc.memories.slice(0, 5).map((memory, idx) => (
                    <div key={idx} className="border-l-2 border-primary pl-3 py-1">
                      <p className="text-sm">{memory.summary}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        回合 {memory.turn_number} • {memory.event_type}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* 对话按钮 */}
        <div className="border-t p-4">
          <Button className="w-full" onClick={() => {
            // TODO: 触发与 NPC 对话的逻辑
            console.log('与 NPC 对话:', npc.name);
          }}>
            <MessageCircle className="w-4 h-4 mr-2" />
            开始对话
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className={cn('h-full bg-background border rounded-lg', className)}>
      {activeNpc ? (
        // 显示选中的 NPC 详情
        renderNpcDetails(activeNpc)
      ) : (
        // 显示 NPC 列表
        <div className="h-full flex flex-col">
          <div className="border-b p-4">
            <h2 className="font-bold text-lg">附近的 NPC</h2>
            <p className="text-sm text-muted-foreground">
              {localNpcs.length} 个可互动角色
            </p>
          </div>
          <ScrollArea className="flex-1 p-4">
            {localNpcs.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <MessageCircle className="w-12 h-12 mb-2" />
                <p className="text-sm">附近没有 NPC</p>
              </div>
            ) : (
              <div className="space-y-3">
                {localNpcs.map(renderNpcCard)}
              </div>
            )}
          </ScrollArea>
        </div>
      )}
    </div>
  );
}
