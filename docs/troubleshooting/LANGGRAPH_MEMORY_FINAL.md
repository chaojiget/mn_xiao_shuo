# LangGraph 长期记忆完整方案

## 概述

本文档总结了使用 LangGraph Checkpoint + Store 实现 DM Agent 长期记忆的完整方案。

## 核心概念

### 1. Checkpoint（对话历史）

**功能**: 自动保存和恢复对话历史

**特点**:
- ✅ 自动保存每一轮对话
- ✅ 自动加载历史（无需手动管理）
- ✅ 持久化到 SQLite
- ✅ 支持时间旅行（回到之前的状态）

**数据存储**:
```
data/checkpoints/dm_memory.db
└── checkpoints 表
    └── thread_id: "session_123"
        └── messages: [
              {role: "user", content: "我叫李明"},
              {role: "assistant", content: "你好李明！"}
            ]
```

### 2. Store（长期记忆）

**功能**: 保存跨会话的长期记忆

**特点**:
- ✅ 保存玩家偏好和习惯
- ✅ 记录重要游戏事件
- ✅ 支持命名空间隔离
- ✅ 跨会话共享

**数据存储**:
```
InMemoryStore (临时) 或 自定义 SQLite Store
└── namespaces:
    ├── player_memories/user_123: {name: "李明", preferences: "探索"}
    └── game_memories/session_123: [{event: "遇到老板娘", location: "酒馆"}]
```

## 架构对比

### 当前方案（game_state.log）

```python
# 手动管理历史
game_state = {
    "log": [
        {"actor": "player", "text": "我把金币扔进柜子"},
        {"actor": "dm", "text": "金币发出叮当声..."}
    ]
}

# 手动构建消息
messages = _build_message_history(game_state, current_action)

# 手动保存
_save_to_log(game_state, player_action, dm_response)
```

**优点**: 简单、与存档集成
**缺点**: 手动管理、无长期记忆

---

### LangGraph 方案（Checkpoint + Store）

```python
async with DMAgentWithMemory() as dm:
    # 对话历史自动保存
    async for event in dm.process_turn(
        session_id="session_123",
        player_action="我把金币扔进柜子",
        user_id="user_456"
    ):
        print(event)

    # 长期记忆通过工具保存
    # DM 会自动调用 save_player_memory、save_game_memory
```

**优点**: 自动管理、支持长期记忆、时间旅行
**缺点**: 与存档分离、需要同步

---

## 完整实现

### 1. DM Agent 实现

文件: `web/backend/agents/dm_agent_with_memory.py`

```python
class DMAgentWithMemory:
    """带长期记忆的 DM Agent"""

    async def __aenter__(self):
        # 初始化 Checkpoint
        self._checkpointer_ctx = AsyncSqliteSaver.from_conn_string(self.checkpoint_db)
        self.checkpointer = await self._checkpointer_ctx.__aenter__()
        return self

    async def process_turn(self, session_id, player_action, user_id):
        # 创建 Agent
        agent = create_agent(
            model=self.model,
            tools=self.tools,
            checkpointer=self.checkpointer,  # 👈 对话历史
            store=self.store,  # 👈 长期记忆
            context_schema=DMContext
        )

        # 配置
        config = {"configurable": {"thread_id": session_id}}
        context = DMContext(session_id=session_id, user_id=user_id)

        # 流式调用（历史会自动加载）
        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": player_action}]},
            config=config,
            context=context,
            version="v2"
        ):
            yield event
```

### 2. 记忆工具

#### 玩家记忆

```python
@tool
def save_player_memory(memory: PlayerMemory, runtime: ToolRuntime[DMContext]) -> str:
    """保存玩家的长期记忆（偏好、习惯等）"""
    store = runtime.store
    user_id = runtime.context.user_id
    store.put(("player_memories",), user_id, memory)
    return "✅ 已保存玩家记忆"

@tool
def recall_player_memory(runtime: ToolRuntime[DMContext]) -> str:
    """回忆玩家的长期记忆"""
    store = runtime.store
    user_id = runtime.context.user_id
    item = store.get(("player_memories",), user_id)
    return item.value if item else "❌ 没有玩家记忆"
```

#### 游戏记忆

```python
@tool
def save_game_memory(memory: GameMemory, runtime: ToolRuntime[DMContext]) -> str:
    """保存重要的游戏事件记忆"""
    store = runtime.store
    session_id = runtime.context.session_id

    import time
    memory_id = f"event_{int(time.time())}"
    store.put(("game_memories", session_id), memory_id, memory)
    return "✅ 已记录事件"

@tool
def recall_game_memories(limit: int = 5, runtime: ToolRuntime[DMContext] = None) -> str:
    """回忆最近的重要游戏事件"""
    store = runtime.store
    session_id = runtime.context.session_id
    items = store.search(("game_memories", session_id))
    return "\n".join([item.value['event'] for item in items[:limit]])
```

### 3. 使用示例

```python
async def main():
    async with DMAgentWithMemory() as dm:
        # 第1回合
        async for event in dm.process_turn(
            session_id="game_001",
            player_action="我叫李明，是一个冒险者",
            user_id="user_123"
        ):
            if event["type"] == "narration":
                print(event["content"])

        # 第2回合（历史会自动恢复）
        async for event in dm.process_turn(
            session_id="game_001",
            player_action="我叫什么名字？",
            user_id="user_123"
        ):
            if event["type"] == "narration":
                print(event["content"])
            # DM 会回答"你叫李明" ✅

        # 新会话，同一个用户（长期记忆会恢复）
        async for event in dm.process_turn(
            session_id="game_002",  # 不同会话
            player_action="你还记得我吗？",
            user_id="user_123"  # 相同用户
        ):
            if event["type"] == "narration":
                print(event["content"])
            # DM 会调用 recall_player_memory，找到"李明" ✅
```

## 记忆层次

### Level 1: 短期记忆（Checkpoint）

- **生命周期**: 单个会话（session）
- **存储内容**: 对话历史
- **自动管理**: ✅ 是
- **示例**: "你刚才说柜子里有金币"

### Level 2: 长期记忆（Store）

- **生命周期**: 跨会话，单个用户
- **存储内容**: 玩家偏好、重要事件
- **自动管理**: ❌ 需要工具调用
- **示例**: "玩家李明喜欢探索"

### Level 3: 永久记忆（Database）

- **生命周期**: 永久
- **存储内容**: 游戏存档、世界状态
- **自动管理**: ❌ 需要手动保存
- **示例**: "玩家在第50回合获得了神器"

## 数据流

```
用户输入 "我叫李明"
    ↓
DMAgent.process_turn()
    ↓
create_agent(checkpointer, store)
    ↓
Agent 自动加载历史（Checkpoint）
    ↓
Agent 调用 save_player_memory（Store）
    ↓
Agent 生成回复："你好李明！"
    ↓
Checkpoint 自动保存对话
    ↓
Store 保存玩家信息

下次会话：
用户输入 "你还记得我吗？"
    ↓
Agent 自动加载历史（找不到，新会话）
    ↓
Agent 调用 recall_player_memory（Store）
    ↓
Store 返回："李明，喜欢探索"
    ↓
Agent 回复："当然记得你，李明！"
```

## 与游戏存档的集成

### 方案1: 独立运行（推荐用于实验）

```python
# Checkpoint 和 Store 独立于游戏存档
async with DMAgentWithMemory() as dm:
    async for event in dm.process_turn(...):
        handle_event(event)

# 游戏存档仍使用 game_state.log
save_service.save_game(game_state)
```

### 方案2: 混合运行（未来优化）

```python
# 保存游戏时，导出 Checkpoint 数据
async def save_game_with_checkpoint(session_id, game_state):
    # 1. 保存游戏状态
    save_service.save_game(game_state)

    # 2. 导出 Checkpoint 对话历史
    async with DMAgentWithMemory() as dm:
        history = await dm.get_conversation_history(session_id)

        # 保存到 game_state.log（作为备份）
        game_state['log'] = [
            {"actor": msg["role"], "text": msg["content"]}
            for msg in history
        ]

        save_service.save_game(game_state)

# 加载游戏时，恢复 Checkpoint
async def load_game_with_checkpoint(save_id):
    game_state = save_service.load_game(save_id)

    # 如果有 log，恢复到 Checkpoint
    if 'log' in game_state:
        async with DMAgentWithMemory() as dm:
            # 重建历史（通过多次调用 agent）
            for entry in game_state['log']:
                if entry['actor'] == 'player':
                    await dm.process_turn(
                        session_id=game_state['session_id'],
                        player_action=entry['text'],
                        user_id=game_state['user_id']
                    )
```

## 性能考虑

### Checkpoint 数据库大小

- 每条消息约 1KB
- 100 回合 ≈ 200 条消息 ≈ 200KB
- 可以定期清理旧 checkpoint

### Store 数据大小

- 玩家记忆：每个用户约 1KB
- 游戏记忆：每个事件约 500B
- InMemoryStore 重启后丢失（可替换为 SQLite Store）

## 推荐使用场景

### 适合使用 LangGraph Memory 的场景：

1. **多人在线游戏**
   - 每个玩家独立的会话
   - 需要跨会话记忆

2. **长期运营的游戏**
   - 玩家可能离开后再回来
   - 需要记住玩家偏好

3. **复杂的NPC关系**
   - NPC需要记住与玩家的互动
   - 需要长期的关系发展

### 不适合的场景：

1. **单机游戏（当前项目）**
   - 存档完整性优先
   - 系统简单可靠

2. **短期游戏**
   - 玩一次就结束
   - 不需要长期记忆

## 文件清单

### 实现文件

- `web/backend/agents/dm_agent_with_memory.py` - DM Agent 实现
- `tests/integration/test_dm_with_memory.py` - 完整测试

### 文档文件

- `docs/troubleshooting/LANGGRAPH_CHECKPOINT_SUCCESS.md` - Checkpoint 测试报告
- `docs/troubleshooting/LANGGRAPH_CHECKPOINT_INTEGRATION.md` - 集成分析
- `docs/troubleshooting/LANGGRAPH_MEMORY_FINAL.md` - 本文档

## 总结

### ✅ LangGraph Memory 的优势

1. **自动管理对话历史** - 无需手动保存和加载
2. **长期记忆支持** - 跨会话记住玩家信息
3. **工具集成** - DM 可以主动保存和回忆记忆
4. **时间旅行** - 可以回到之前的对话状态

### ⚠️ 需要注意的问题

1. **与存档分离** - Checkpoint 和游戏存档是两个数据库
2. **需要同步** - 保存游戏时需要导出 Checkpoint 数据
3. **复杂度增加** - 需要管理两套系统

### 💡 推荐策略

**对于当前的单人跑团游戏项目**：

1. **继续使用 game_state.log** 作为主要方案
2. **DMAgentWithMemory 作为可选功能** 用于实验和开发
3. **未来迁移路径清晰** - 可以逐步迁移到 LangGraph Memory

**代码示例**：

```python
# 默认使用当前方案
from agents.dm_agent_langchain import DMAgentLangChain
dm = DMAgentLangChain()

# 可选：使用长期记忆方案
from agents.dm_agent_with_memory import DMAgentWithMemory
async with DMAgentWithMemory() as dm:
    # ... 使用 DM
```

## 相关资源

- [LangGraph Persistence 官方文档](https://langchain-ai.github.io/langgraph/how-tos/persistence/)
- [AsyncSqliteSaver API](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver)
- [LangChain Agent with Memory](https://python.langchain.com/docs/how_to/chatbots_memory/)
