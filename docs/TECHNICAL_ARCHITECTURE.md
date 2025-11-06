# 技术架构详解

> AI跑团游戏系统 - 深度技术文档
> 更新时间: 2025-11-05

## 📑 目录

- [架构概览](#架构概览)
- [LangChain集成](#langchain集成)
- [流式输出实现](#流式输出实现)
- [存档系统设计](#存档系统设计)
- [状态管理](#状态管理)
- [性能优化](#性能优化)

---

## 架构概览

### 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层                                │
│  Next.js 14 + TypeScript + Zustand                         │
│  - 页面渲染 (SSR/CSR)                                       │
│  - 组件复用                                                 │
│  - 状态持久化                                               │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP/SSE
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      业务逻辑层                              │
│  FastAPI + LangChain 1.0                                   │
│  - API路由处理                                              │
│  - 游戏引擎逻辑                                             │
│  - AI Agent调度                                             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据 & AI 层                            │
│  SQLite + OpenRouter (LangChain ChatOpenAI)                │
│  - 数据持久化                                               │
│  - LLM推理                                                  │
└─────────────────────────────────────────────────────────────┘
```

### 技术选型理由

| 技术 | 选型理由 |
|------|----------|
| **Next.js 14** | App Router 支持 SSR/CSR 混合，性能优秀 |
| **LangChain 1.0** | 统一的 LLM 框架，丰富的工具生态 |
| **OpenRouter** | 一个 API 访问多个模型，降低依赖 |
| **Zustand** | 轻量级状态管理，自带持久化 |
| **shadcn/ui** | 高质量 Headless UI，可定制 |
| **SQLite** | 轻量级，无需额外服务，适合单机游戏 |
| **uv** | Python 包管理器，比 pip 快 10-100 倍 |

---

## LangChain集成

### 1. Agent 架构

```python
# dm_agent_langchain.py

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

class DMAgentLangChain:
    def __init__(self, model_name: str = None):
        # 初始化 OpenRouter 模型
        self.model = ChatOpenAI(
            model="deepseek/deepseek-v3.1-terminus",
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=0.7,
            max_tokens=4096,
            streaming=True  # 开启流式
        )

        # 游戏工具
        self.tools = ALL_GAME_TOOLS

    async def process_turn(self, session_id, player_action, game_state):
        # 构建系统提示词
        system_prompt = self._build_system_prompt(game_state)

        # 创建 agent
        agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=system_prompt
        )

        # 调用 agent
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": player_action}]
        })

        return result
```

**关键点:**
- ✅ 使用 `create_agent` 简化 agent 创建
- ✅ `streaming=True` 启用流式输出
- ✅ 工具列表直接传入 `tools` 参数

### 2. 工具定义

```python
# game_tools_langchain.py

from langchain.tools import tool

@tool
def add_item(item_name: str, quantity: int = 1, description: str = "") -> dict:
    """给予玩家物品

    Args:
        item_name: 物品名称
        quantity: 数量（默认1）
        description: 物品描述

    Returns:
        {"success": bool, "item": str, "quantity": int}
    """
    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)

    if not state:
        return {"success": False, "error": "游戏状态未初始化"}

    # 添加到背包
    item = InventoryItem(
        id=item_name.lower().replace(" ", "_"),
        name=item_name,
        description=description,
        quantity=quantity,
        type="misc"
    )

    state.player.inventory.append(item)

    return {
        "success": True,
        "item": item_name,
        "quantity": quantity,
        "message": f"获得 {item_name} x{quantity}"
    }

# 导出所有工具
ALL_GAME_TOOLS = [
    get_player_state,
    add_item,
    remove_item,
    # ... 共15个工具
]
```

**工具调用流程:**

```
LLM 决定调用工具
    ↓
返回 tool_call: {
    "name": "add_item",
    "arguments": {
        "item_name": "火把",
        "quantity": 3
    }
}
    ↓
LangChain 自动执行工具
    ↓
add_item.invoke({
    "item_name": "火把",
    "quantity": 3
})
    ↓
返回结果给 LLM
    ↓
LLM 生成叙事
```

### 3. System Prompt 工程

```python
def _build_system_prompt(self, game_state: Dict[str, Any]) -> str:
    return f"""你是一个单人跑团游戏的游戏主持人（DM）。

世界设定:
{game_state.get('world', {}).get('theme', '奇幻世界')}

当前状态:
- 位置: {game_state.get('world', {}).get('current_location', '未知')}
- 回合数: {game_state.get('turn_number', 0)}

你的职责:
1. 描述场景和环境（生动且富有细节）
2. 管理NPC互动和对话
3. 处理玩家行动的后果
4. 使用工具调用来更新游戏状态

❗ 关键规则（必须遵守）:
1. **物品操作规则**:
   - 玩家扔掉/使用/丢弃物品 → 必须调用 `remove_item` 工具
   - 玩家获得物品 → 必须调用 `add_item` 工具

2. **叙事连贯性规则**:
   - 阅读"最近发生"中的事件，**必须延续上一回合的场景**
   - 不要突然跳转到其他场景

3. **描述详细度**:
   - 每个场景至少200字
   - 包含：视觉、听觉、触觉、气味等感官细节
"""
```

**Prompt 优化历程:**

| 版本 | 问题 | 改进 |
|------|------|------|
| v1.0 | 物品不减少 | 添加"必须调用 remove_item" |
| v1.1 | 场景跳转 | 添加"延续上一回合场景" |
| v1.2 | 描述太短 | 要求 200-400 字 + 感官细节 |
| v1.3 | Context优先级混乱 | 将"最近发生"移到最前 |

---

## 流式输出实现

### 1. 后端流式生成

```python
# game_engine.py

async def process_turn_stream(
    self,
    request: GameTurnRequest
) -> AsyncIterator[Dict[str, Any]]:
    """处理游戏回合（流式）"""
    try:
        # 1. 先完整处理回合
        response = await self.process_turn(request)

        # 2. 将旁白按句子分割
        sentences = response.narration.split("。")
        for sentence in sentences:
            if sentence.strip():
                # 逐句发送
                yield {
                    "type": "text",
                    "content": sentence + "。"
                }
                # 可选：添加延迟模拟打字效果
                # await asyncio.sleep(0.1)

        # 3. 发送actions
        for action in response.actions:
            yield {
                "type": "action",
                "action": action
            }

        # 4. 发送完成信号
        yield {
            "type": "done",
            "metadata": {
                "hints": response.hints,
                "suggestions": response.suggestions,
                "turn": request.currentState.world.time
            }
        }

    except Exception as e:
        yield {
            "type": "error",
            "error": str(e)
        }
```

**为什么不直接流式调用LLM?**

目前实现是先完整处理，再分句发送。优点：
- ✅ 简单可靠
- ✅ 可以在发送前验证完整性
- ✅ 确保工具调用完成后再发送

未来优化方向：
- 🔄 真正的流式调用 LLM
- 🔄 实时发送 LLM token
- 🔄 并行执行工具调用

### 2. FastAPI SSE 端点

```python
# game_api.py

@router.post("/turn/stream")
async def process_turn_stream(request: GameTurnRequestModel):
    """处理游戏回合（流式）"""
    async def generate():
        try:
            state = GameState(**request.currentState)

            turn_request = GameTurnRequest(
                playerInput=request.playerInput,
                currentState=state
            )

            # 流式生成
            async for chunk in game_engine.process_turn_stream(turn_request):
                # 发送 SSE 格式数据
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

            # 发送最终状态
            yield f"data: {json.dumps({'type': 'state', 'state': state.model_dump()}, ensure_ascii=False)}\n\n"

        except Exception as e:
            error_data = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

**SSE 格式:**
```
data: {"type": "text", "content": "你向北走去。"}

data: {"type": "text", "content": "前方出现一座城门。"}

data: {"type": "done", "metadata": {...}}

data: {"type": "state", "state": {...}}


```

### 3. 前端流式接收

```typescript
// DmInterface.tsx

const handleSendMessage = async () => {
  const response = await fetch(`${apiUrl}/api/game/turn/stream`, {
    method: 'POST',
    body: JSON.stringify({ playerInput, currentState })
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  let buffer = '';
  let fullNarration = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    // 解码
    buffer += decoder.decode(value, { stream: true });

    // 处理 SSE 格式
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));

        if (data.type === 'text') {
          fullNarration += data.content;
          setStreamingText(fullNarration); // 实时更新UI
        }
      }
    }
  }

  // 完成后添加到历史
  setMessages(prev => [...prev, {
    role: 'assistant',
    content: fullNarration
  }]);
};
```

**关键技术:**
- `ReadableStream` - 流式读取响应
- `TextDecoder` - 解码字节流
- Buffer 管理 - 处理不完整的行

---

## 存档系统设计

### 1. 数据库 Schema

```sql
-- 游戏存档表
CREATE TABLE game_saves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    slot_id INTEGER NOT NULL,        -- 0=自动, 1-10=手动
    save_name TEXT NOT NULL,
    game_state TEXT NOT NULL,        -- JSON序列化
    metadata TEXT,                   -- 元数据
    screenshot_url TEXT,             -- 可选截图
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, slot_id)         -- 同一用户的同一槽位唯一
);

-- 索引优化
CREATE INDEX idx_user_id ON game_saves(user_id);
CREATE INDEX idx_slot_id ON game_saves(slot_id);
CREATE INDEX idx_updated_at ON game_saves(updated_at);
```

**为什么使用 TEXT 存储 JSON?**
- SQLite 没有原生 JSON 类型
- TEXT + JSON序列化足够简单高效
- 支持 JSON 函数 (SQLite 3.38+)

### 2. SaveService 实现

```python
# save_service.py

class SaveService:
    def save_game(
        self,
        user_id: str,
        slot_id: int,
        save_name: str,
        game_state: Dict[str, Any],
        auto_save: bool = False
    ) -> int:
        """保存游戏"""
        # 验证槽位
        if not 0 <= slot_id <= 10:
            raise ValueError("槽位必须在 0-10 之间")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 提取元数据
            metadata = {
                "turn_number": game_state.get("turn_number", 0),
                "location": game_state.get("player", {}).get("location"),
                "hp": game_state.get("player", {}).get("hp"),
            }

            # 序列化
            game_state_json = json.dumps(game_state, ensure_ascii=False)
            metadata_json = json.dumps(metadata, ensure_ascii=False)

            # Upsert (插入或更新)
            cursor.execute("""
                INSERT INTO game_saves (user_id, slot_id, save_name, game_state, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, slot_id) DO UPDATE SET
                    save_name = excluded.save_name,
                    game_state = excluded.game_state,
                    metadata = excluded.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, slot_id, save_name, game_state_json, metadata_json))

            save_id = cursor.lastrowid
            conn.commit()

            return save_id

        finally:
            conn.close()

    def get_latest_auto_save(self, user_id: str):
        """获取最新自动保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, game_state, metadata, created_at
                FROM game_saves
                WHERE user_id = ? AND slot_id = 0
                ORDER BY updated_at DESC
                LIMIT 1
            """, (user_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "auto_save_id": row[0],
                "game_state": json.loads(row[1]),
                "turn_number": json.loads(row[2]).get("turn_number"),
                "created_at": row[3]
            }

        finally:
            conn.close()
```

### 3. 自动保存触发

```python
# game_api.py

@router.post("/turn")
async def process_turn(request: GameTurnRequestModel):
    # ... 处理回合 ...

    # 自动保存
    if save_service:
        try:
            auto_save_id = save_service.save_game(
                user_id="default_user",
                slot_id=0,
                save_name="自动保存",
                game_state=state.model_dump(),
                auto_save=True
            )
            print(f"[DEBUG] 💾 自动保存成功: {auto_save_id}")
        except Exception as e:
            print(f"[WARNING] 自动保存失败: {e}")
            # 不阻断游戏流程
```

**自动保存策略:**
- ✅ 每回合自动触发
- ✅ 保存到槽位0（专用）
- ✅ 失败不影响游戏
- ✅ 只保留最新一份

### 4. 前端恢复机制

```typescript
// page.tsx

useEffect(() => {
  const loadOrInitGame = async () => {
    try {
      // 1. 尝试加载自动保存
      const autoSave = await apiClient.getLatestAutoSave();

      if (autoSave.success && autoSave.game_state) {
        // 2. 恢复状态
        setGameState(autoSave.game_state);
        setSessionId(autoSave.game_state.session_id || `session_${Date.now()}`);

        // 3. 提示用户
        toast({
          title: "✅ 进度已恢复",
          description: `继续第 ${autoSave.game_state.turn_number || 0} 回合的冒险`
        });
      } else {
        // 没有自动保存，初始化新游戏
        await initGame();
      }
    } catch (error) {
      // 加载失败，初始化新游戏
      await initGame();
    }
  };

  loadOrInitGame();
}, []);
```

**DmInterface 历史恢复:**

```typescript
// DmInterface.tsx

useEffect(() => {
  if (gameState?.log && gameState.log.length > 0 && messages.length === 0) {
    console.log('[DmInterface] 恢复历史消息:', gameState.log.length);

    const historicalMessages = gameState.log.map((entry, index) => ({
      id: `history_${index}`,
      role: entry.actor === 'player' ? 'player' : 'dm',
      content: entry.text,
      timestamp: new Date(entry.timestamp || Date.now())
    }));

    setMessages(historicalMessages);
  }
}, [gameState]);
```

---

## 状态管理

### 1. Zustand Store

```typescript
// gameStore.ts

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface GameStore {
  gameState: GameState | null;
  setGameState: (state: GameState) => void;
  resetGame: () => void;
}

export const useGameStore = create<GameStore>()(
  persist(
    (set) => ({
      gameState: null,

      setGameState: (state) => {
        console.log('[GameStore] 💾 保存游戏状态到 localStorage');
        set({ gameState: state });
      },

      resetGame: () => {
        console.log('[GameStore] 🗑️ 清除游戏进度');
        set({ gameState: null });
      }
    }),
    {
      name: 'game-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // 只保存 gameState，不保存 UI 状态
        gameState: state.gameState
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.gameState) {
          console.log('[GameStore] 🔄 从 localStorage 恢复游戏进度');
        }
      }
    }
  )
);
```

**为什么选择 Zustand?**
- ✅ 比 Redux 轻量（~1KB）
- ✅ 不需要 Provider
- ✅ 内置 persist 中间件
- ✅ TypeScript 支持好

### 2. 双层存储策略

```
┌─────────────────────────────────────┐
│          浏览器端                    │
│  ┌────────────────────────────┐    │
│  │  Zustand Store (内存)      │    │
│  │  - 当前游戏状态             │    │
│  │  - UI 状态                  │    │
│  └───────────┬────────────────┘    │
│              │ persist             │
│              ▼                     │
│  ┌────────────────────────────┐    │
│  │  localStorage              │    │
│  │  - 缓存游戏状态 (仅前端)   │    │
│  └────────────────────────────┘    │
└─────────────────────────────────────┘
              │ API
              ▼
┌─────────────────────────────────────┐
│          服务器端                    │
│  ┌────────────────────────────┐    │
│  │  SQLite Database           │    │
│  │  - 持久化存档（可靠）       │    │
│  │  - 支持多槽位               │    │
│  └────────────────────────────┘    │
└─────────────────────────────────────┘
```

**为什么需要双层?**
- localStorage: 快速恢复，减少网络请求
- SQLite: 可靠持久化，支持跨设备（未来）

**同步策略:**
- 每回合后端自动保存到 SQLite
- 前端 Zustand 同步更新 localStorage
- 页面加载时优先从后端加载

---

## 性能优化

### 1. 前端优化

**组件优化:**
```typescript
// 使用 React.memo 避免不必要的渲染
export const DmMessage = React.memo(({ message }) => {
  return <div>{message.content}</div>;
});

// 使用 useCallback 缓存回调
const handleSendMessage = useCallback(async () => {
  // ...
}, [gameState, input]);
```

**虚拟滚动:**
```typescript
// 对于长消息列表，考虑使用虚拟滚动
import { useVirtualizer } from '@tanstack/react-virtual';

const rowVirtualizer = useVirtualizer({
  count: messages.length,
  getScrollElement: () => scrollRef.current,
  estimateSize: () => 100,
});
```

**代码分割:**
```typescript
// 懒加载非首屏组件
const WorldMap = lazy(() => import('@/components/game/WorldMap'));
```

### 2. 后端优化

**异步优化:**
```python
# 使用 asyncio.gather 并行执行
async def process_turn(self, request):
    # 并行执行多个异步任务
    results = await asyncio.gather(
        self.llm_backend.generate(...),
        self.db.save_state(...),
        return_exceptions=True
    )
```

**数据库连接池:**
```python
# 使用连接池（未来优化）
from sqlalchemy.pool import QueuePool

pool = QueuePool(
    creator=lambda: sqlite3.connect(db_path),
    pool_size=5,
    max_overflow=10
)
```

**缓存 System Prompt:**
```python
# 缓存不变的 System Prompt 部分
@lru_cache(maxsize=1)
def get_base_system_prompt():
    return """你是一个游戏主持人..."""
```

### 3. 流式输出优化

**分批发送:**
```python
# 不是逐字发送，而是按句子发送
sentences = narration.split("。")
for sentence in sentences:
    yield {"type": "text", "content": sentence + "。"}
    # 可选延迟
    await asyncio.sleep(0.05)
```

**压缩传输:**
```python
# 对于大数据，使用 gzip 压缩
from fastapi.responses import StreamingResponse
import gzip

async def compressed_stream():
    async for chunk in generate():
        compressed = gzip.compress(chunk.encode())
        yield compressed

return StreamingResponse(
    compressed_stream(),
    headers={"Content-Encoding": "gzip"}
)
```

---

## 监控与调试

### 1. 日志系统

**后端日志配置:**
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

# 使用
logger.info("🎮 开始处理游戏回合")
logger.debug(f"📝 玩家输入: {player_input}")
logger.error(f"❌ 错误: {error}")
```

**前端日志:**
```typescript
// 统一的日志函数
const log = {
  info: (msg: string) => console.log(`[Game] ℹ️ ${msg}`),
  error: (msg: string) => console.error(`[Game] ❌ ${msg}`),
  debug: (msg: string) => console.debug(`[Game] 🐛 ${msg}`)
};

log.info('游戏初始化完成');
```

### 2. 性能监控

```typescript
// 测量 API 响应时间
const startTime = performance.now();
await apiClient.processTurn(...);
const endTime = performance.now();
console.log(`API 响应时间: ${endTime - startTime}ms`);
```

### 3. 错误追踪

```python
# 使用 traceback 打印完整错误堆栈
try:
    # ...
except Exception as e:
    logger.error(f"错误: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
```

---

## 安全考虑

### 1. API 安全

**环境变量保护:**
```bash
# 敏感信息不提交到 git
.env
.env.local
```

**请求验证:**
```python
from pydantic import BaseModel, validator

class GameTurnRequest(BaseModel):
    playerInput: str
    currentState: GameState

    @validator('playerInput')
    def validate_input(cls, v):
        if len(v) > 1000:
            raise ValueError('输入过长')
        return v
```

### 2. XSS 防护

```typescript
// React 自动转义，但要注意 dangerouslySetInnerHTML
<div>{message.content}</div>  // ✅ 安全

// 如果必须使用 HTML
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{
  __html: DOMPurify.sanitize(html)
}} />
```

### 3. SQL 注入防护

```python
# 使用参数化查询
cursor.execute(
    "SELECT * FROM game_saves WHERE user_id = ?",
    (user_id,)  # ✅ 安全
)

# 不要拼接 SQL
cursor.execute(
    f"SELECT * FROM game_saves WHERE user_id = '{user_id}'"  # ❌ 危险
)
```

---

## 未来优化方向

### 短期优化
- [ ] 真正的流式 LLM 调用（实时 token）
- [ ] WebSocket 替代 SSE（双向通信）
- [ ] 存档截图功能
- [ ] 批量加载历史消息（分页）

### 中期优化
- [ ] 多用户支持（用户认证）
- [ ] 云端存档（S3/OSS）
- [ ] 向量数据库（语义搜索）
- [ ] Redis 缓存层

### 长期优化
- [ ] 服务器部署（Docker + K8s）
- [ ] 负载均衡
- [ ] 实时多人模式
- [ ] AI 模型微调

---

**文档维护**: Claude Code
**最后更新**: 2025-11-05
**版本**: 1.0
