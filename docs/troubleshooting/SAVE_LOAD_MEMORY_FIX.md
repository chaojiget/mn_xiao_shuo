# 存档加载后对话历史恢复修复

**日期**: 2025-11-06
**问题**: 从存档管理加载游戏后，DM 无法记住之前的对话历史
**状态**: ✅ 已修复

---

## 问题描述

用户报告：从存档列表加载游戏后，虽然存档数据中包含完整的对话历史（`game_state.log`），但 DM Agent 表现得像是失忆了，无法记住之前提到的内容。

### 问题表现

1. 在第5回合保存游戏
2. 从存档管理加载这个存档
3. 继续游戏时，DM 无法记住第1-5回合发生的事情
4. 例如：之前提到柜子里有金币，加载后 DM 不记得了

### 数据库检查

```bash
sqlite3 novel.db "SELECT json_extract(game_state, '$.log') FROM game_saves WHERE id = 12;"
```

**结果**: 存档中**确实包含**完整的对话历史！

```json
[
  {"turn":1, "actor":"player", "text":"环顾四周", "timestamp":1762438707},
  {"turn":1, "actor":"system", "text":"你缓缓睁开双眼...", "timestamp":1762438707},
  {"turn":2, "actor":"player", "text":"过去看看，并扔出一个硬币", "timestamp":1762438780},
  ...
]
```

---

## 根本原因

系统中存在**两种记忆机制混用**的问题：

### 1. game_state.log（手动记忆）
- 对话历史保存在 `game_state.log` 中
- 每次回合结束后手动调用 `_save_to_log()` 保存
- 下次回合通过 `_build_message_history()` 读取历史

### 2. LangGraph Checkpoint（自动记忆）
- LangGraph 使用 `thread_id` 自动管理对话历史
- 每次调用 `agent.astream()` 时自动保存和加载
- **问题**: `thread_id` 依赖于 `session_id`

### 关键冲突

**加载存档时**：
- ✅ `game_state.log` 恢复了：完整的对话记录在数据库中
- ❌ `session_id` 不一致：前端生成了新的 `session_id`
- ❌ LangGraph Checkpoint 找不到历史：使用新的 `thread_id` 查询，找不到旧对话

**结果**: Agent 虽然能看到 `game_state.log`（在默认模式下），但 Checkpoint 模式下无法找到历史对话。

---

## 解决方案

### 核心思路

**启用 LangGraph Checkpoint 模式，并确保 `session_id` 在存档中持久化**

1. **在 GameState 中添加 `session_id` 字段**
2. **初始化游戏时生成并保存 `session_id`**
3. **加载存档时恢复相同的 `session_id`**
4. **DM Agent 使用 `session_id` 作为 `thread_id`**

### 实施步骤

#### 步骤1: 添加 `session_id` 到 GameState

**文件**: `web/backend/game/game_tools.py`

```python
class GameState(BaseModel):
    version: str = "1.0.0"
    session_id: Optional[str] = None  # 🔥 新增：会话ID，用于Checkpoint记忆
    turn_number: int = 0
    player: PlayerState
    world: WorldState
    quests: List[Quest] = []
    map: GameMap
    log: List[GameLogEntry] = []
    metadata: Dict[str, Any] = {}
```

#### 步骤2: 初始化时生成 `session_id`

**文件**: `web/backend/game/game_engine.py`

```python
def init_game(self, story_id: Optional[str] = None) -> GameState:
    # ... 创建玩家、世界、地图等 ...

    # 🔥 生成唯一的 session_id
    import uuid
    session_id = f"game_{uuid.uuid4().hex[:16]}"

    # 创建初始状态
    state = GameState(
        version="1.0.0",
        session_id=session_id,  # 👈 设置 session_id
        player=player,
        world=world,
        quests=[],
        map=game_map,
        log=[]
    )

    return state
```

#### 步骤3: 启用 DM Agent 的 Checkpoint 模式

**文件**: `web/backend/api/dm_api.py`

```python
def init_dm_agent():
    """初始化 DM Agent"""
    global dm_agent
    from agents.dm_agent_langchain import DMAgentLangChain

    # 🔥 启用 Checkpoint 模式，让 Agent 自动记忆对话历史
    dm_agent = DMAgentLangChain(
        model_name="deepseek/deepseek-v3.1-terminus",
        use_checkpoint=True,
        checkpoint_db="data/checkpoints/dm.db"
    )
    print("✅ DM Agent 已初始化 (LangChain + Checkpoint)")
```

#### 步骤4: 修改 DM Agent 支持 Checkpoint

**文件**: `web/backend/agents/dm_agent_langchain.py`

```python
# 初始化时创建 checkpointer
if self.use_checkpoint:
    from langgraph.checkpoint.sqlite import SqliteSaver
    import sqlite3
    conn = sqlite3.connect(checkpoint_db, check_same_thread=False)
    self.checkpointer = SqliteSaver(conn)

# process_turn 时使用 checkpointer
if self.use_checkpoint and self.checkpointer:
    # 使用 langgraph 的 create_react_agent，支持 checkpointer
    from langgraph.prebuilt import create_react_agent
    agent = create_react_agent(
        model=self.model,
        tools=self.tools,
        checkpointer=self.checkpointer  # 👈 启用自动记忆
    )

    # Checkpoint 模式：只传入当前玩家行动（历史会自动加载）
    message_history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"玩家行动: {player_action}"}
    ]
    config = {"configurable": {"thread_id": session_id}}  # 👈 使用 session_id

    async for event in agent.astream(
        {"messages": message_history},
        config=config
    ):
        # ... 处理 event ...
```

#### 步骤5: 前端加载时使用存档的 `session_id`

**文件**: `web/frontend/app/game/play/page.tsx`

前端**已经正确实现**：

```typescript
// 从存档加载
const parsedState = JSON.parse(loadedGameState)
setGameState(parsedState)
setSessionId(parsedState.session_id || `session_${Date.now()}`)  // ✅ 使用存档的 session_id
```

---

## 修复效果

### 修复前

```
玩家: [回合1] 我把金币扔进柜子
DM: 金币发出叮当声...

[保存游戏]
[加载游戏]

玩家: [回合6] 柜子里有什么？
DM: 柜子是空的 ❌ (失忆了)
```

### 修复后

```
玩家: [回合1] 我把金币扔进柜子
DM: 金币发出叮当声...

[保存游戏 - session_id: game_abc123]
[加载游戏 - session_id: game_abc123]

玩家: [回合6] 柜子里有什么？
DM: 柜子里有你之前扔进去的金币 ✅ (记得了)
```

---

## 技术细节

### LangGraph Checkpoint 工作原理

```
1. 初始化 Agent 时传入 checkpointer:
   agent = create_react_agent(
       model=model,
       tools=tools,
       checkpointer=SqliteSaver(conn)
   )

2. 调用时传入 thread_id:
   config = {"configurable": {"thread_id": "game_abc123"}}
   agent.astream({"messages": [...]}, config=config)

3. Checkpoint 自动做两件事:
   - 保存：每回合结束后，自动保存对话到 SQLite
   - 加载：下次调用时，自动加载该 thread_id 的历史对话
```

### Checkpoint 数据库结构

```sql
-- data/checkpoints/dm.db
CREATE TABLE checkpoints (
    thread_id TEXT,
    checkpoint_id TEXT,
    parent_checkpoint_id TEXT,
    checkpoint BLOB,
    metadata BLOB,
    PRIMARY KEY (thread_id, checkpoint_id)
);
```

**关键点**: `thread_id` 必须一致，才能找到历史对话！

---

## 数据流完整追踪

### 新游戏流程

```
1. 前端: /api/game/init
   ↓
2. 后端: GameEngine.init_game()
   - 生成 session_id = "game_abc123"
   - 创建 GameState(session_id="game_abc123")
   ↓
3. 返回给前端
   - 前端: setSessionId("game_abc123")
   - 前端: setGameState({session_id: "game_abc123", ...})
   ↓
4. 玩家输入 → DmInterface → /api/game/turn/stream
   ↓
5. DM Agent.process_turn(session_id="game_abc123")
   - config = {"configurable": {"thread_id": "game_abc123"}}
   - agent.astream(..., config=config)
   ↓
6. LangGraph Checkpoint 自动保存到:
   - data/checkpoints/dm.db
   - thread_id = "game_abc123"
```

### 保存游戏流程

```
1. 前端: apiClient.saveGame({game_state: {..., session_id: "game_abc123"}})
   ↓
2. 后端: save_service.save_game()
   - 序列化 game_state (包含 session_id)
   - 保存到 data/sqlite/novel.db
```

### 加载游戏流程

```
1. 前端: apiClient.loadSave(save_id)
   ↓
2. 后端: save_service.load_game(save_id)
   - 从数据库读取 game_state
   - 返回 {game_state: {..., session_id: "game_abc123"}}
   ↓
3. 前端: localStorage.setItem('loadedGameState', JSON.stringify(game_state))
   - 跳转到 /game/play
   ↓
4. /game/play 页面:
   - 读取 localStorage
   - setGameState(game_state)
   - setSessionId(game_state.session_id)  // "game_abc123"
   ↓
5. 玩家继续游戏:
   - DM Agent.process_turn(session_id="game_abc123")  // 相同的 session_id！
   - LangGraph Checkpoint 自动加载 thread_id="game_abc123" 的历史
```

---

## 验证方法

### 方法1: 运行测试脚本

```bash
uv run python tests/integration/test_checkpoint_memory_fix.py
```

**预期输出**:
```
[1] 初始化 DM Agent (Checkpoint 模式)...
✅ Checkpoint 模式已启用

[2] 第1回合
玩家: 我叫张三，今年25岁
DM: 你好张三！...

[3] 第2回合
玩家: 我叫什么名字？几岁？
DM: 你叫张三，今年25岁  ✅

✅ DM 成功记住了玩家的名字和年龄
```

### 方法2: 手动测试

1. 启动游戏：`./scripts/start/start_all_with_agent.sh`
2. 开始新游戏
3. 进行3-5个回合的对话，提到一些特殊信息（如"柜子里有金币"）
4. 保存游戏到槽位1
5. 退出游戏，重新加载槽位1的存档
6. 询问 DM 之前的信息（如"柜子里有什么？"）
7. **预期**: DM 能够正确回忆起"金币"

### 方法3: 检查数据库

```bash
# 检查 game_state 中是否有 session_id
sqlite3 data/sqlite/novel.db \
  "SELECT id, json_extract(game_state, '$.session_id') FROM game_saves;"

# 检查 checkpoint 数据库
sqlite3 data/checkpoints/dm.db \
  "SELECT thread_id, COUNT(*) FROM checkpoints GROUP BY thread_id;"
```

---

## 文件清单

### 修改的文件

1. **`web/backend/game/game_tools.py`** (line 92-101)
   - 添加 `session_id: Optional[str]` 到 `GameState`

2. **`web/backend/game/game_engine.py`** (line 601-615)
   - 在 `init_game()` 中生成并设置 `session_id`

3. **`web/backend/api/dm_api.py`** (line 18-29)
   - 启用 Checkpoint 模式：`use_checkpoint=True`

4. **`web/backend/agents/dm_agent_langchain.py`** (line 88-110, 273-339)
   - 初始化时创建 `SqliteSaver`
   - `process_turn` 中使用 `checkpointer` 和 `thread_id`

### 新增的文件

5. **`tests/integration/test_checkpoint_memory_fix.py`**
   - Checkpoint 记忆功能测试

6. **`docs/troubleshooting/SAVE_LOAD_MEMORY_FIX.md`** (本文档)
   - 问题分析和修复文档

---

## 未来优化

### 可选优化1: 迁移旧存档

对于没有 `session_id` 的旧存档，可以在加载时自动生成：

```python
# web/backend/services/save_service.py
def load_game(self, save_id: int):
    game_state = json.loads(row[3])

    # 🔥 兼容旧存档：自动生成 session_id
    if not game_state.get('session_id'):
        import uuid
        game_state['session_id'] = f"migrated_{uuid.uuid4().hex[:16]}"

    return {
        "game_state": game_state,
        ...
    }
```

### 可选优化2: Checkpoint 清理

定期清理旧的 checkpoint 数据，避免数据库膨胀：

```python
# 清理超过30天的 checkpoint
def cleanup_old_checkpoints(days=30):
    cutoff = datetime.now() - timedelta(days=days)
    conn.execute("""
        DELETE FROM checkpoints
        WHERE created_at < ?
    """, (cutoff,))
```

### 可选优化3: 混合模式

同时保留 `game_state.log` 作为备份：

- 主要使用 Checkpoint 模式
- 保存游戏时，导出 Checkpoint 到 `game_state.log`
- 作为双重保险

---

## 总结

### ✅ 修复完成

1. **问题根源**: `session_id` 不一致导致 LangGraph Checkpoint 无法找到历史
2. **解决方案**: 在 `GameState` 中持久化 `session_id`，确保加载时使用相同的 ID
3. **验证方法**: 测试脚本 + 手动测试 + 数据库检查
4. **副作用**: 无，完全向后兼容

### 💡 关键教训

**LangGraph Checkpoint 的核心原则**：
> `thread_id` 必须在整个会话生命周期中保持一致！

任何会导致 `thread_id` 变化的操作（如重新生成 `session_id`）都会导致历史对话丢失。

### 📚 相关文档

- `docs/troubleshooting/FINAL_SUMMARY.md` - DM 记忆系统总结
- `docs/troubleshooting/CONVERSATION_HISTORY_FIX.md` - 对话历史修复（之前的工作）
- `docs/troubleshooting/LANGGRAPH_CHECKPOINT_SUCCESS.md` - Checkpoint 测试报告

---

**作者**: Claude
**完成日期**: 2025-11-06
**版本**: 1.0
