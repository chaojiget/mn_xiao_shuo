/**
 * 游戏状态管理 Store (Zustand)
 */

import { create } from 'zustand';
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

export const useGameStore = create<GameStore>((set) => ({
  // 初始状态
  gameState: null,
  quests: [],
  npcs: [],
  activeNpc: null,
  isLoading: false,
  error: null,
  isConnected: false,

  // 游戏状态管理
  setGameState: (state) => set({ gameState: state }),

  updateGameState: (updates) => set((state) => ({
    gameState: state.gameState ? { ...state.gameState, ...updates } : null
  })),

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
  resetGame: () => set({
    gameState: null,
    quests: [],
    npcs: [],
    activeNpc: null,
    isLoading: false,
    error: null,
    isConnected: false
  })
}));
