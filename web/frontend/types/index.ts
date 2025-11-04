export interface Message {
  role: "user" | "assistant" | "system"
  content: string
  timestamp: Date
  isStreaming?: boolean
  character?: string
}

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

export interface Novel {
  id: string
  title: string
  type: "scifi" | "xianxia"
  chapters: number
  created_at: string
  updated_at?: string
  protagonist?: string
  background?: string
  settings?: NovelSettings
}

export interface GenerateSettingParams {
  title: string
  novel_type: "scifi" | "xianxia"
}

export interface ChatParams {
  message: string
  novel_settings: NovelSettings
  history: Omit<Message, 'timestamp' | 'isStreaming'>[]
}

export interface StreamChunk {
  type: "text" | "done"
  content?: string
}