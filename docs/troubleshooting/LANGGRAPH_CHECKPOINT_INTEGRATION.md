# LangGraph Checkpoint 集成方案

## 概述

LangGraph 提供了官方的检查点（Checkpoint）机制来持久化对话状态。本文档探讨是否应该集成这个功能到我们的游戏系统中。

## LangGraph Checkpoint 是什么？

LangGraph Checkpoint 是 LangGraph 官方提供的状态持久化机制，用于：
- 保存 Agent 的完整执行状态
- 支持暂停和恢复 Agent 执行
- 实现时间旅行（回到之前的状态）
- 自动管理消息历史

### 可用的 Checkpoint 库

```bash
# 基础接口（已安装）
langgraph-checkpoint

# SQLite 实现（刚刚安装）
langgraph-checkpoint-sqlite

# PostgreSQL 实现（生产环境）
langgraph-checkpoint-postgres
```

## 使用示例

### 基本用法

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# 创建 SQLite checkpoint saver
checkpoint_db_path = "data/checkpoints/game_checkpoints.db"
memory = SqliteSaver.from_conn_string(checkpoint_db_path)

# 创建带 checkpoint 的 Agent
model = ChatOpenAI(model="deepseek/deepseek-v3.1-terminus")
agent = create_agent(
    model=model,
    tools=tools,
    checkpointer=memory  # 👈 添加 checkpoint
)

# 使用特定 thread_id 运行（等同于我们的 session_id）
config = {"configurable": {"thread_id": "game_session_123"}}

# 第一次对话
result1 = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "我把金币扔进柜子"}]},
    config=config
)

# 第二次对话 - 会自动加载之前的历史！
result2 = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "柜子里有什么？"}]},
    config=config  # 相同的 thread_id，会自动恢复上下文
)
```

### 高级功能

```python
# 1. 获取特定时间点的状态
state_snapshot = await memory.aget(config)
print(state_snapshot.values)  # 完整的状态

# 2. 获取历史检查点列表
checkpoints = await memory.alist(config)
for checkpoint in checkpoints:
    print(f"Checkpoint at {checkpoint.checkpoint_id}")

# 3. 回到之前的状态（时间旅行）
config_with_checkpoint = {
    "configurable": {
        "thread_id": "game_session_123",
        "checkpoint_id": "previous_checkpoint_id"
    }
}
result = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "继续"}]},
    config_with_checkpoint
)
```

## 方案对比

### 方案A：当前实现（game_state.log）

```python
# 当前做法
game_state = {
    "log": [
        {"actor": "player", "text": "我把金币扔进柜子"},
        {"actor": "dm", "text": "金币发出叮当声..."}
    ]
}

# 手动构建消息历史
messages = _build_message_history(game_state, current_action)

# 手动保存新对话
_save_to_log(game_state, player_action, dm_response)
```

**优点：**
- ✅ 完全控制存储格式
- ✅ 与游戏状态紧密集成
- ✅ 存档时自动包含对话历史
- ✅ 简单直观

**缺点：**
- ❌ 手动管理历史
- ❌ 没有时间旅行功能
- ❌ 缺少检查点快照

---

### 方案B：LangGraph Checkpoint（纯 Checkpoint）

```python
# 使用 LangGraph Checkpoint
from langgraph.checkpoint.sqlite import SqliteSaver

memory = SqliteSaver.from_conn_string("checkpoints.db")

agent = create_agent(
    model=model,
    tools=tools,
    checkpointer=memory
)

# 对话会自动保存
result = await agent.ainvoke(
    {"messages": [...]},
    config={"configurable": {"thread_id": session_id}}
)
```

**优点：**
- ✅ 官方标准，自动管理
- ✅ 内置时间旅行
- ✅ 支持暂停/恢复执行
- ✅ 无需手动保存历史

**缺点：**
- ❌ 与 game_state 分离（两个数据库）
- ❌ 存档时需要同步 checkpoint
- ❌ 增加系统复杂度
- ❌ Checkpoint 数据库独立于游戏数据库

---

### 方案C：混合方案（推荐）

将两者结合，发挥各自优势：

```python
# 1. 使用 LangGraph Checkpoint 管理对话历史
memory = SqliteSaver.from_conn_string("data/checkpoints.db")

agent = create_agent(
    model=model,
    tools=tools,
    checkpointer=memory
)

# 2. 保存游戏状态时，导出 checkpoint 数据
async def save_game(session_id, game_state, slot_id):
    # 保存游戏状态到 SQLite
    save_service.save_game(
        user_id="default_user",
        slot_id=slot_id,
        game_state=game_state
    )

    # 🔥 导出 checkpoint 历史到存档
    config = {"configurable": {"thread_id": session_id}}
    checkpoint = await memory.aget(config)

    # 将 checkpoint 数据保存到 game_state
    game_state['checkpoint_data'] = {
        'messages': checkpoint.values.get('messages', []),
        'checkpoint_id': checkpoint.checkpoint_id
    }

    # 更新存档
    save_service.save_game(..., game_state=game_state)

# 3. 加载游戏时，恢复 checkpoint
async def load_game(save_id):
    save_data = save_service.load_game(save_id)
    game_state = save_data['game_state']

    # 🔥 恢复 checkpoint 数据
    if 'checkpoint_data' in game_state:
        config = {"configurable": {"thread_id": session_id}}

        # 重建历史（如果 checkpoint 不存在）
        messages = game_state['checkpoint_data']['messages']
        await agent.ainvoke(
            {"messages": messages},
            config=config
        )

    return game_state
```

**优点：**
- ✅ 获得 LangGraph 的自动历史管理
- ✅ 支持时间旅行和调试
- ✅ 存档仍然包含完整对话（作为备份）
- ✅ 兼容现有系统

**缺点：**
- ⚠️ 需要维护两个数据库的同步
- ⚠️ 代码复杂度增加

---

## 数据库结构对比

### 当前方案（game_state.log）

```
game.db (SQLite)
└── game_saves
    └── game_state (JSON)
        └── log: [
              {actor: "player", text: "...", timestamp: 123},
              {actor: "dm", text: "...", timestamp: 124}
            ]
```

### LangGraph Checkpoint 方案

```
game.db (SQLite)          checkpoints.db (SQLite)
└── game_saves            └── checkpoints
    └── game_state            └── thread_id: "session_123"
        └── player: {...}         └── values:
            world: {...}              └── messages: [...]
                                          state: {...}
```

### 混合方案

```
game.db (SQLite)
└── game_saves
    └── game_state (JSON)
        ├── player: {...}
        ├── world: {...}
        └── checkpoint_data: {        # 备份 checkpoint
              messages: [...],
              checkpoint_id: "..."
            }

checkpoints.db (SQLite)
└── checkpoints
    └── thread_id: "session_123"
        └── values:
            └── messages: [...]      # 主要的对话历史
                state: {...}
```

---

## 性能对比

| 操作 | 当前方案 | LangGraph Checkpoint | 混合方案 |
|------|---------|---------------------|---------|
| **保存对话** | O(1) - 追加到数组 | O(1) - SQLite INSERT | O(1) + O(1) |
| **读取历史** | O(n) - 遍历数组 | O(1) - SQLite 查询 | O(1) |
| **存档游戏** | O(1) - JSON 序列化 | O(n) - 需要导出 checkpoint | O(n) |
| **加载存档** | O(1) - JSON 反序列化 | O(n) - 需要重建 checkpoint | O(n) |
| **时间旅行** | ❌ 不支持 | ✅ O(1) | ✅ O(1) |

---

## 推荐方案

### 对于我们的游戏项目：继续使用当前方案（game_state.log）

**理由：**

1. **存档完整性优先** - 游戏存档必须包含完整对话历史，LangGraph Checkpoint 需要额外同步
2. **简单可靠** - 当前实现已经验证可行，测试通过
3. **性能足够** - 对于单人游戏，对话历史不会太长（<1000条）
4. **调试便利** - 直接查看 SQLite 即可看到完整对话

### 何时考虑迁移到 LangGraph Checkpoint？

满足以下条件时可以考虑：

1. **需要多用户并发** - 多个玩家同时游戏
2. **需要时间旅行** - 回到之前的对话状态进行分支探索
3. **对话历史超长** - 单个会话超过 1000 条对话
4. **需要分布式部署** - 多服务器共享状态

---

## 未来优化方向

即使继续使用当前方案，我们可以借鉴 LangGraph Checkpoint 的一些设计：

### 1. 添加快照功能（类似 Checkpoint）

```python
# 在关键时刻创建快照
def create_snapshot(game_state, label=""):
    snapshot = {
        "snapshot_id": str(uuid.uuid4()),
        "timestamp": int(time.time()),
        "label": label,
        "game_state": copy.deepcopy(game_state),
        "log_length": len(game_state['log'])
    }

    save_service.create_snapshot(
        save_id=current_save_id,
        turn_number=game_state['turn_number'],
        game_state=snapshot
    )

# 使用示例
create_snapshot(game_state, label="进入地下城前")
create_snapshot(game_state, label="获得神器后")
```

### 2. 添加日志压缩

```python
# 定期压缩旧日志
def compress_old_logs(game_state, keep_recent=50):
    """保留最近 N 条 + 摘要"""
    if len(game_state['log']) <= keep_recent:
        return

    old_logs = game_state['log'][:-keep_recent]
    recent_logs = game_state['log'][-keep_recent:]

    # 使用 LLM 生成摘要
    summary = llm.summarize_conversation(old_logs)

    game_state['log'] = [
        {
            "actor": "system",
            "text": f"[之前 {len(old_logs)} 条对话的摘要]\n{summary}",
            "timestamp": old_logs[-1]['timestamp']
        }
    ] + recent_logs
```

### 3. 添加分支探索（可选）

```python
# 允许玩家回到之前的状态并创建分支
def create_branch(save_id, from_turn_number, branch_name):
    """从某个回合创建新分支"""
    original_state = save_service.load_snapshot(save_id, from_turn_number)

    new_branch = {
        "branch_name": branch_name,
        "parent_save_id": save_id,
        "parent_turn": from_turn_number,
        "game_state": original_state
    }

    return save_service.save_game(..., game_state=new_branch)
```

---

## 实现示例（如果未来需要集成）

如果未来确实需要 LangGraph Checkpoint，这是集成代码：

```python
# web/backend/agents/dm_agent_langchain.py

from langgraph.checkpoint.sqlite import SqliteSaver
from pathlib import Path

class DMAgentLangChain:
    def __init__(self, model_name: str = None, use_checkpoint: bool = False):
        # ... 现有初始化代码

        # 🔥 可选启用 checkpoint
        self.checkpointer = None
        if use_checkpoint:
            checkpoint_db = Path("data/checkpoints/dm_checkpoints.db")
            checkpoint_db.parent.mkdir(parents=True, exist_ok=True)
            self.checkpointer = SqliteSaver.from_conn_string(str(checkpoint_db))
            logger.info(f"✅ LangGraph Checkpoint 已启用: {checkpoint_db}")

    async def process_turn(self, session_id, player_action, game_state):
        # 创建 agent（带 checkpoint）
        agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=system_prompt,
            checkpointer=self.checkpointer  # 👈 添加 checkpoint
        )

        # 配置 thread_id
        config = {
            "configurable": {
                "thread_id": session_id
            }
        }

        # 调用 agent（会自动保存到 checkpoint）
        async for event in agent.astream_events(
            {"messages": message_history},
            config=config,  # 👈 传递 config
            version="v2"
        ):
            # ... 处理事件

        # 如果使用 checkpoint，可以不再手动保存到 log
        if not self.checkpointer:
            self._save_to_log(game_state, player_action, full_narration)
```

---

## 总结

### 当前决策：继续使用 game_state.log

✅ **不需要立即迁移到 LangGraph Checkpoint**

**原因：**
1. 当前方案已验证可行
2. 存档完整性优先
3. 系统简单可靠
4. 性能足够

### 未来可以考虑：

1. **借鉴思想**：添加快照、压缩、分支功能
2. **渐进式迁移**：先作为可选功能（`use_checkpoint=True`）
3. **混合方案**：同时使用两者，发挥各自优势

---

## 相关资源

- [LangGraph Checkpoint 官方文档](https://langchain-ai.github.io/langgraph/how-tos/persistence/)
- [SqliteSaver API 文档](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.sqlite.SqliteSaver)
- 我们的实现：`web/backend/agents/dm_agent_langchain.py:122-151`
- 对话存储对比：`docs/troubleshooting/CONVERSATION_STORAGE_COMPARISON.md`
