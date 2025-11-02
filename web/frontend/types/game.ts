/**
 * 游戏核心数据类型定义
 * 单人跑团游戏的所有状态、协议、工具接口
 */

// ==================== 玩家状态 ====================

export interface PlayerState {
  hp: number                    // 生命值
  maxHp: number                 // 最大生命值
  stamina: number               // 体力/精力
  maxStamina: number            // 最大体力
  traits: string[]              // 特质/技能
  inventory: InventoryItem[]    // 背包物品
  location: string              // 当前位置ID
  money?: number                // 金钱/货币
}

export interface InventoryItem {
  id: string                    // 物品唯一ID
  name: string                  // 物品名称
  description: string           // 物品描述
  quantity: number              // 数量
  type: ItemType                // 物品类型
  properties?: Record<string, any>  // 额外属性
}

export type ItemType = "weapon" | "armor" | "consumable" | "key" | "quest" | "misc"

// ==================== 任务系统 ====================

export interface Quest {
  id: string                    // 任务ID
  title: string                 // 任务标题
  description: string           // 任务描述
  status: QuestStatus           // 任务状态
  hints: string[]               // 提示信息
  objectives?: QuestObjective[] // 任务目标
  rewards?: QuestReward         // 奖励
  triggerConditions?: Condition // 触发条件
}

export type QuestStatus = "inactive" | "active" | "completed" | "failed"

export interface QuestObjective {
  id: string
  description: string
  completed: boolean
  required: boolean             // 是否必须完成
}

export interface QuestReward {
  exp?: number
  money?: number
  items?: string[]              // 物品ID列表
}

export interface Condition {
  flags?: Record<string, boolean>    // 需要的标志位
  items?: string[]                   // 需要的物品
  location?: string                  // 需要的位置
  questsCompleted?: string[]         // 需要完成的任务
}

// ==================== 世界状态 ====================

export interface WorldState {
  time: number                  // 游戏时间（回合数或时间戳）
  flags: Record<string, boolean | number | string>  // 全局标志位
  discoveredLocations: string[] // 已发现的地点
  variables: Record<string, any>  // 自定义变量
  currentScene?: string         // 当前场景ID
}

// ==================== 地图系统 ====================

export interface GameMap {
  nodes: MapNode[]              // 地点节点
  edges: MapEdge[]              // 通路边
  currentNodeId: string         // 当前节点ID
}

export interface MapNode {
  id: string                    // 节点ID
  name: string                  // 地点名称
  shortDesc: string             // 简短描述
  discovered: boolean           // 是否已发现
  locked: boolean               // 是否锁定
  keyRequired?: string          // 需要的钥匙物品ID
  metadata?: Record<string, any>  // 额外元数据
}

export interface MapEdge {
  from: string                  // 起点节点ID
  to: string                    // 终点节点ID
  bidirectional: boolean        // 是否双向
  condition?: Condition         // 通行条件
}

// ==================== 游戏日志 ====================

export interface GameLogEntry {
  turn: number                  // 回合数
  actor: "player" | "system" | "npc"  // 行动者
  text: string                  // 文本内容
  timestamp: number             // 时间戳
  metadata?: Record<string, any>  // 额外元数据
}

// ==================== 完整游戏状态 ====================

export interface GameState {
  version: string               // 版本号（用于存档兼容）
  player: PlayerState           // 玩家状态
  world: WorldState             // 世界状态
  quests: Quest[]               // 任务列表
  map: GameMap                  // 地图
  log: GameLogEntry[]           // 游戏日志
  metadata?: {
    createdAt: number
    updatedAt: number
    playTime: number            // 游玩时长（秒）
  }
}

// ==================== 行动协议 ====================

/**
 * 游戏回合响应：文本旁白 + 可执行行动分离
 */
export interface GameTurnResponse {
  narration: string             // 旁白文本（流式渲染）
  actions: GameAction[]         // 状态变更行动列表
  hints?: string[]              // 提示信息（显示在任务区）
  suggestions?: string[]        // 行动建议chips
  metadata?: {
    tokensUsed?: number
    processingTime?: number
  }
}

/**
 * 游戏行动：所有状态变更的原子操作
 */
export type GameAction =
  | { type: "ADD_ITEM"; itemId: string; quantity?: number }
  | { type: "REMOVE_ITEM"; itemId: string; quantity?: number }
  | { type: "UPDATE_HP"; delta: number }
  | { type: "UPDATE_STAMINA"; delta: number }
  | { type: "SET_LOCATION"; locationId: string }
  | { type: "SET_FLAG"; key: string; value: boolean | number | string }
  | { type: "UPDATE_QUEST"; questId: string; updates: Partial<Quest> }
  | { type: "DISCOVER_LOCATION"; locationId: string }
  | { type: "UNLOCK_LOCATION"; locationId: string }
  | { type: "ADD_TRAIT"; trait: string }
  | { type: "REMOVE_TRAIT"; trait: string }
  | { type: "ADD_LOG"; entry: Omit<GameLogEntry, "turn" | "timestamp"> }
  | { type: "CUSTOM"; key: string; payload: any }

// ==================== 工具系统 ====================

/**
 * Agent可用的工具函数接口
 */
export interface GameTools {
  // 状态读取
  getState: () => GameState
  getPlayerState: () => PlayerState
  getWorldState: () => WorldState
  getQuests: (filter?: { status?: QuestStatus }) => Quest[]
  getLocation: (locationId?: string) => MapNode | null

  // 状态修改（通过patch）
  setState: (patch: Partial<GameState>) => void
  updatePlayer: (patch: Partial<PlayerState>) => void
  updateWorld: (patch: Partial<WorldState>) => void

  // 检定系统
  rollCheck: (params: RollCheckParams) => RollCheckResult

  // 记忆查询
  queryMemory: (query: string, limit?: number) => GameLogEntry[]

  // 事件发射
  emitEvent: (event: GameEvent) => void
}

export interface RollCheckParams {
  type: CheckType               // 检定类型
  dc: number                    // 难度等级 (Difficulty Class)
  modifier?: number             // 修正值
  advantage?: boolean           // 优势（掷两次取高）
  disadvantage?: boolean        // 劣势（掷两次取低）
}

export type CheckType =
  | "survival"      // 生存
  | "stealth"       // 潜行
  | "persuasion"    // 说服
  | "perception"    // 感知
  | "strength"      // 力量
  | "intelligence"  // 智力
  | "luck"          // 幸运
  | "custom"        // 自定义

export interface RollCheckResult {
  success: boolean              // 是否成功
  roll: number                  // 骰点结果
  total: number                 // 总值（骰点+修正）
  dc: number                    // 目标难度
  margin: number                // 差值（成功为正，失败为负）
  critical?: boolean            // 是否大成功/大失败
}

export interface GameEvent {
  type: string
  payload: any
  timestamp?: number
}

// ==================== 存档系统 ====================

export interface SaveSlot {
  id: string                    // 存档槽ID
  name: string                  // 存档名称
  state: GameState              // 游戏状态
  thumbnail?: string            // 缩略图（可选）
  checksum?: string             // 校验和（防篡改）
  savedAt: number               // 保存时间戳
}

export interface SaveMetadata {
  slots: Record<string, SaveSlot>  // 存档槽映射
  autoSave?: SaveSlot              // 自动存档
  lastPlayed?: string              // 最后游玩的槽ID
}

// ==================== 规则引擎 ====================

/**
 * 规则引擎：拦截不合法行动
 */
export interface GameRule {
  id: string
  name: string
  description: string
  condition: (state: GameState, action: GameAction) => boolean
  effect: (state: GameState, action: GameAction) => GameTurnResponse | null
}

// ==================== NPC系统 ====================

export interface NPC {
  id: string
  name: string
  role: string                  // 角色定位
  personality: string[]         // 性格标签
  tone: string                  // 口吻/说话风格
  knownInfo: string[]           // 已知信息
  forbiddenInfo: string[]       // 禁止透露的信息
  location?: string             // 所在位置
  relationship?: number         // 与玩家的关系（-100到100）
}

// ==================== 剧情编辑器 ====================

export interface StoryNode {
  id: string
  type: "scene" | "choice" | "check" | "event"
  title: string
  content: string               // 场景描述/选项文本
  triggers?: Condition          // 触发条件
  effects?: GameAction[]        // 执行效果
  next?: string[]               // 下一个节点ID列表
  metadata?: Record<string, any>
}

export interface StoryGraph {
  nodes: StoryNode[]
  startNodeId: string
  metadata: {
    title: string
    author: string
    version: string
    description: string
  }
}

// ==================== API请求/响应 ====================

export interface GameTurnRequest {
  playerInput: string           // 玩家输入
  currentState: GameState       // 当前状态
  context?: {
    recentLogs?: GameLogEntry[] // 近期日志
    relevantMemories?: GameLogEntry[]  // 相关记忆
  }
}

export interface InitGameRequest {
  storyId?: string              // 剧情ID（可选）
  playerConfig?: Partial<PlayerState>  // 玩家配置
  worldConfig?: Partial<WorldState>    // 世界配置
}

export interface InitGameResponse {
  state: GameState
  narration: string             // 开场旁白
  suggestions?: string[]
}
