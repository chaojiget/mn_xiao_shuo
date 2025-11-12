/**
 * 游戏组件统一导出
 */

export { NarrativeInterface } from './NarrativeInterface';
// 兼容旧命名，避免外部引用断裂
export { NarrativeInterface as DmInterface } from './NarrativeInterface';
export { QuestTracker } from './QuestTracker';
export { NpcDialog } from './NpcDialog';
export { GameStatePanel } from './GameStatePanel';
