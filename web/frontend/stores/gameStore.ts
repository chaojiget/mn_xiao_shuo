/**
 * 游戏状态管理 Store (Zustand)
 * 支持自动保存到 localStorage
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { GameState, Quest, NPC } from '@/types/game';

interface GameStore {
  // 游戏状态
  gameState: GameState | null;
  setGameState: (state: GameState) => void;
  updateGameState: (updates: Partial<GameState>) => void;

  // 任务
  quests: Quest[];
  setQuests: (quests: Quest[]) => void;
  addQuest: (quest: Quest) => void;
  updateQuest: (questId: string, updates: Partial<Quest>) => void;

  // NPC
  npcs: NPC[];
  setNpcs: (npcs: NPC[]) => void;
  updateNpc: (npcId: string, updates: Partial<NPC>) => void;

  // 当前对话的 NPC
  activeNpc: NPC | null;
  setActiveNpc: (npc: NPC | null) => void;

  // 加载状态
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  // 错误状态
  error: string | null;
  setError: (error: string | null) => void;

  // WebSocket 连接状态
  isConnected: boolean;
  setIsConnected: (connected: boolean) => void;

  // 重置游戏
  resetGame: () => void;
}

export const useGameStore = create<GameStore>()(
  persist(
    (set) => ({
      // 初始状态
      gameState: null,
      quests: [],
      npcs: [],
      activeNpc: null,
      isLoading: false,
      error: null,
      isConnected: false,

      // 游戏状态管理
      setGameState: (state) => {
        console.log('[GameStore] 💾 保存游戏状态到 localStorage');
        set({ gameState: state });
      },

      updateGameState: (updates) => set((state) => {
        console.log('[GameStore] 💾 更新游戏状态:', Object.keys(updates));
        return {
          gameState: state.gameState ? { ...state.gameState, ...updates } : null
        };
      }),

      // 任务管理
      setQuests: (quests) => set({ quests }),

      addQuest: (quest) => set((state) => ({
        quests: [...state.quests, quest]
      })),

      updateQuest: (questId, updates) => set((state) => ({
        quests: state.quests.map(q =>
          q.quest_id === questId ? { ...q, ...updates } : q
        )
      })),

      // NPC 管理
      setNpcs: (npcs) => set({ npcs }),

      updateNpc: (npcId, updates) => set((state) => ({
        npcs: state.npcs.map(npc =>
          npc.npc_id === npcId ? { ...npc, ...updates } : npc
        )
      })),

      setActiveNpc: (npc) => set({ activeNpc: npc }),

      // UI 状态
      setIsLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),
      setIsConnected: (connected) => set({ isConnected: connected }),

      // 重置
      resetGame: () => {
        console.log('[GameStore] 🗑️  清除游戏进度');
        set({
          gameState: null,
          quests: [],
          npcs: [],
          activeNpc: null,
          isLoading: false,
          error: null,
          isConnected: false
        });
      }
    }),
    {
      name: 'game-storage', // localStorage key
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // 只保存这些字段到 localStorage
        gameState: state.gameState,
        quests: state.quests,
        npcs: state.npcs,
        // 不保存 UI 状态（isLoading, error, isConnected）
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.gameState) {
          console.log('[GameStore] 🔄 从 localStorage 恢复游戏进度');
          console.log('[GameStore] 📊 回合数:', state.gameState.world?.time || 0);
        } else {
          console.log('[GameStore] ℹ️  没有保存的游戏进度');
        }
      }
    }
  )
);
