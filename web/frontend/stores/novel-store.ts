/**
 * 小说全局状态管理 - Zustand Store
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Novel, NovelSettings, Message, ConversationBranch } from '@/lib/types'

interface NovelStore {
  // 当前小说
  currentNovel: NovelSettings | null
  setCurrentNovel: (novel: NovelSettings | null) => void
  updateNovelSettings: (updates: Partial<NovelSettings>) => void

  // 小说列表
  novels: Novel[]
  setNovels: (novels: Novel[]) => void
  addNovel: (novel: Novel) => void

  // 对话消息
  messages: Message[]
  setMessages: (messages: Message[]) => void
  addMessage: (message: Message) => void
  updateLastMessage: (content: string) => void
  clearMessages: () => void

  // 对话分支
  branches: ConversationBranch[]
  currentBranchId: string | null
  createBranch: (fromMessageIndex: number, name?: string) => string
  switchBranch: (branchId: string) => void
  deleteBranch: (branchId: string) => void

  // UI 状态
  isSettingsPanelOpen: boolean
  setSettingsPanelOpen: (open: boolean) => void

  // 活跃的 NPC（当前场景）
  activeNPCs: string[]
  setActiveNPCs: (npcIds: string[]) => void
}

export const useNovelStore = create<NovelStore>()(
  persist(
    (set, get) => ({
      // 当前小说
      currentNovel: null,
      setCurrentNovel: (novel) => set({ currentNovel: novel }),
      updateNovelSettings: (updates) =>
        set((state) => ({
          currentNovel: state.currentNovel
            ? { ...state.currentNovel, ...updates }
            : null,
        })),

      // 小说列表
      novels: [],
      setNovels: (novels) => set({ novels }),
      addNovel: (novel) =>
        set((state) => ({
          novels: [novel, ...state.novels],
        })),

      // 对话消息
      messages: [],
      setMessages: (messages) => set({ messages }),
      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),
      updateLastMessage: (content) =>
        set((state) => {
          const messages = [...state.messages]
          const lastMessage = messages[messages.length - 1]
          if (lastMessage && lastMessage.role === 'assistant') {
            lastMessage.content = content
          }
          return { messages }
        }),
      clearMessages: () => set({ messages: [] }),

      // 对话分支
      branches: [],
      currentBranchId: null,

      createBranch: (fromMessageIndex, name) => {
        const state = get()
        const branchId = `branch_${Date.now()}`
        const messages = state.messages.slice(0, fromMessageIndex + 1)

        const newBranch: ConversationBranch = {
          id: branchId,
          parentId: state.currentBranchId,
          messages: messages.map(m => ({ ...m })),
          createdAt: new Date(),
          name: name || `分支 ${state.branches.length + 1}`,
        }

        set((state) => ({
          branches: [...state.branches, newBranch],
          currentBranchId: branchId,
          messages: newBranch.messages,
        }))

        return branchId
      },

      switchBranch: (branchId) => {
        const state = get()
        const branch = state.branches.find((b) => b.id === branchId)
        if (branch) {
          set({
            currentBranchId: branchId,
            messages: branch.messages.map(m => ({ ...m })),
          })
        }
      },

      deleteBranch: (branchId) =>
        set((state) => ({
          branches: state.branches.filter((b) => b.id !== branchId),
          currentBranchId:
            state.currentBranchId === branchId
              ? null
              : state.currentBranchId,
        })),

      // UI 状态
      isSettingsPanelOpen: true,
      setSettingsPanelOpen: (open) => set({ isSettingsPanelOpen: open }),

      // 活跃的 NPC
      activeNPCs: [],
      setActiveNPCs: (npcIds) => set({ activeNPCs: npcIds }),
    }),
    {
      name: 'novel-store', // localStorage key
      partialize: (state) => ({
        // 只持久化这些字段
        currentNovel: state.currentNovel,
        novels: state.novels,
        messages: state.messages,
        branches: state.branches,
        currentBranchId: state.currentBranchId,
      }),
    }
  )
)
