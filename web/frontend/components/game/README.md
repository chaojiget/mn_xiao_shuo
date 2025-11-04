# 游戏组件文档

React/Next.js 游戏界面组件，用于单人跑团游戏（DM Agent 模式）。

## 组件列表

### 1. DmInterface - DM 交互界面

**文件**: `DmInterface.tsx`

**功能**:
- 聊天界面显示 DM 叙述和玩家输入
- WebSocket 实时连接（自动降级到 HTTP）
- 流式文本显示
- 工具调用可视化
- 消息历史记录

**Props**:
```typescript
{
  sessionId?: string;      // 游戏会话 ID（用于 WebSocket）
  className?: string;      // 自定义样式
}
```

**使用示例**:
```tsx
import { DmInterface } from '@/components/game';

<DmInterface sessionId={sessionId} />
```

**API 依赖**:
- `POST /api/game/turn` - 同步发送玩家行动
- `WS /api/dm/ws/{session_id}` - WebSocket 实时连接（可选）

---

### 2. QuestTracker - 任务追踪器

**文件**: `QuestTracker.tsx`

**功能**:
- 显示当前激活的任务
- 任务目标进度条
- 任务完成动画
- 按状态分类（激活/可接取/已完成）
- 任务奖励预览

**Props**:
```typescript
{
  className?: string;      // 自定义样式
}
```

**使用示例**:
```tsx
import { QuestTracker } from '@/components/game';

<QuestTracker />
```

**API 依赖**:
- `GET /api/game/quests` - 获取任务列表
- `GET /api/game/quests?status=active` - 按状态筛选

**任务状态**:
- `available` - 可接取
- `active` - 激活中
- `completed` - 已完成
- `failed` - 已失败

---

### 3. NpcDialog - NPC 对话组件

**文件**: `NpcDialog.tsx`

**功能**:
- 显示附近的 NPC 列表
- NPC 详细信息（描述、性格、目标）
- 关系指示器（好感度/信任度）
- NPC 记忆查看
- 点击开始对话

**Props**:
```typescript
{
  className?: string;      // 自定义样式
}
```

**使用示例**:
```tsx
import { NpcDialog } from '@/components/game';

<NpcDialog />
```

**API 依赖**:
- `GET /api/game/npcs?status=active` - 获取 NPC 列表
- `GET /api/game/npcs?location=xxx` - 按位置筛选

**关系等级**:
- `stranger` - 陌生人 (灰色)
- `acquaintance` - 熟人 (蓝色)
- `friend` - 朋友 (绿色)
- `ally` - 盟友 (紫色)
- `enemy` - 敌人 (红色)

---

### 4. GameStatePanel - 游戏状态面板

**文件**: `GameStatePanel.tsx`

**功能**:
- HP 和资源显示
- 背包管理
- 物品详情查看
- 位置信息
- 游戏元数据（回合数、会话 ID）

**Props**:
```typescript
{
  className?: string;      // 自定义样式
  compact?: boolean;       // 紧凑模式（侧边栏适用）
}
```

**使用示例**:
```tsx
import { GameStatePanel } from '@/components/game';

// 完整模式
<GameStatePanel />

// 紧凑模式（侧边栏）
<GameStatePanel compact />
```

**两种模式**:
- **完整模式**: 显示标签页（状态/背包）
- **紧凑模式**: 仅显示关键状态信息

---

## 状态管理

所有组件使用 Zustand store 管理状态:

**Store 位置**: `stores/gameStore.ts`

**关键状态**:
```typescript
{
  gameState: GameState | null;        // 游戏状态
  quests: Quest[];                    // 任务列表
  npcs: NPC[];                        // NPC 列表
  activeNpc: NPC | null;              // 当前选中的 NPC
  isLoading: boolean;                 // 加载状态
  error: string | null;               // 错误信息
  isConnected: boolean;               // WebSocket 连接状态
}
```

**使用示例**:
```tsx
import { useGameStore } from '@/stores/gameStore';

function MyComponent() {
  const { gameState, setGameState } = useGameStore();

  // 使用状态...
}
```

---

## 类型定义

**位置**: `types/game.ts`

**核心类型**:
- `GameState` - 游戏状态
- `Quest` - 任务
- `NPC` - NPC
- `InventoryItem` - 物品
- `NPCRelationship` - NPC 关系
- `DmMessage` - DM 消息

---

## 主页面布局

**文件**: `app/game/play/page.tsx`

**布局结构**:
```
┌─────────────────────────────────────────────────┐
│ 顶部工具栏 (保存/退出)                           │
├─────────┬──────────────────────┬────────────────┤
│ 左侧栏  │   DM 界面 (主要)     │   右侧栏        │
│         │                      │                │
│ 游戏    │   - 消息历史         │   - 任务追踪    │
│ 状态    │   - 流式叙述         │   - NPC 列表    │
│         │   - 玩家输入         │                │
│ (桌面)  │   - 工具调用         │   (桌面)        │
└─────────┴──────────────────────┴────────────────┘
│ 移动端底部导航 (状态/任务/NPC)                   │
└─────────────────────────────────────────────────┘
```

**响应式设计**:
- **桌面 (lg+)**: 三栏布局，所有功能可见
- **平板**: 主 DM 界面 + 底部导航
- **手机**: 全屏 DM 界面 + 底部导航

---

## API 端点

### 游戏初始化
```
POST /api/game/init
```

### 游戏回合
```
POST /api/game/turn         # 同步模式
POST /api/game/turn/stream  # 流式模式
```

### WebSocket
```
WS /api/dm/ws/{session_id}
```

### 任务系统
```
GET    /api/game/quests
POST   /api/game/quests/{quest_id}/activate
PUT    /api/game/quests/{quest_id}/progress
POST   /api/game/quests/{quest_id}/complete
```

### NPC 系统
```
GET    /api/game/npcs
PUT    /api/game/npcs/{npc_id}/relationship
POST   /api/game/npcs/{npc_id}/memories
```

### 存档系统
```
POST   /api/game/save
GET    /api/game/saves/{user_id}
GET    /api/game/save/{save_id}
DELETE /api/game/save/{save_id}
```

---

## 开发注意事项

### 1. WebSocket 连接

DmInterface 会自动尝试 WebSocket 连接，失败时降级到 HTTP：
```typescript
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${protocol}//${window.location.host}/api/dm/ws/${sessionId}`;
```

### 2. 状态同步

所有组件通过 Zustand store 同步状态，避免重复请求：
```typescript
// 在一个组件中更新
setGameState(newState);

// 其他组件自动响应
const { gameState } = useGameStore();
```

### 3. 错误处理

使用 toast 显示错误信息：
```typescript
import { useToast } from '@/hooks/use-toast';

const { toast } = useToast();

toast({
  title: '错误',
  description: '操作失败',
  variant: 'destructive',
});
```

### 4. 动画效果

使用 Framer Motion 实现流畅动画：
```typescript
import { motion, AnimatePresence } from 'framer-motion';

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0 }}
>
  {/* 内容 */}
</motion.div>
```

---

## 扩展指南

### 添加新的游戏工具

1. 在后端添加工具函数 (`web/backend/agents/game_tools_mcp.py`)
2. 在 DmInterface 中处理工具调用消息
3. 更新类型定义 (`types/game.ts`)

### 添加新的状态指标

1. 更新 `GameState` 类型
2. 在 GameStatePanel 中添加显示逻辑
3. 更新后端 API 返回数据

### 自定义主题

使用 Tailwind CSS 自定义颜色：
```typescript
className="bg-primary text-primary-foreground"
```

---

## 测试

### 组件测试
```bash
# 启动开发服务器
cd web/frontend
npm run dev
```

### 完整流程测试
```bash
# 启动所有服务
./scripts/start/start_all_with_agent.sh

# 访问游戏页面
http://localhost:3000/game/play
```

---

## 常见问题

### Q: WebSocket 无法连接？
A: 检查后端是否实现了 WebSocket 路由，或使用 HTTP 模式（自动降级）。

### Q: 任务/NPC 不显示？
A: 检查后端 API 是否正常返回数据，查看浏览器控制台错误。

### Q: 状态不同步？
A: 确保所有组件都使用 `useGameStore` hook，而不是本地状态。

### Q: 移动端布局混乱？
A: 检查响应式类名 (`lg:`, `xl:` 等) 是否正确应用。

---

## 更新日志

### 2025-11-04
- ✅ 创建 DmInterface 组件（WebSocket + HTTP）
- ✅ 创建 QuestTracker 组件（任务追踪）
- ✅ 创建 NpcDialog 组件（NPC 对话）
- ✅ 创建 GameStatePanel 组件（状态面板）
- ✅ 创建游戏主页面（响应式布局）
- ✅ 集成 Zustand 状态管理
- ✅ 添加 Framer Motion 动画
