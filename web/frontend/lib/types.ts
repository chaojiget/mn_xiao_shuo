/**
 * 全局类型定义
 */

export interface NPC {
  id: string
  name: string
  role: string
  personality: string
  background: string
}

export interface NovelSettings {
  id?: string
  title: string
  type: "scifi" | "xianxia"
  protagonist: string
  background: string
  protagonistName?: string
  protagonistRole?: string
  protagonistAbilities?: string[]
  npcs?: NPC[]
}

export interface Message {
  role: "user" | "assistant" | "system"
  content: string
  timestamp: Date
  isStreaming?: boolean
  character?: string
}

export interface Novel {
  id: string
  title: string
  type: "scifi" | "xianxia"
  chapters: number
  created_at: string
  updated_at?: string
  settings?: NovelSettings
}

export interface ConversationBranch {
  id: string
  parentId: string | null
  messages: Message[]
  createdAt: Date
  name?: string
}

export interface StoryEvent {
  turn: number
  summary: string
  importance: "low" | "medium" | "high"
  timestamp: Date
}
