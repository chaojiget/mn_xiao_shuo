# DM Agent 升级指南 - 添加 Checkpoint 支持

## 变更概述

`DMAgentLangChain` 现在支持两种模式：

1. **默认模式**（推荐）: 使用 `game_state.log` 手动管理对话历史
2. **Checkpoint 模式**（可选）: 使用 LangGraph Checkpoint 自动管理

## 新的初始化参数

```python
from agents.dm_agent_langchain import DMAgentLangChain

# 默认模式（无变化）
dm = DMAgentLangChain()

# 或者显式指定模式
dm = DMAgentLangChain(
    model_name="deepseek",
    use_checkpoint=False  # 默认值
)

# Checkpoint 模式（可选）
dm = DMAgentLangChain(
    model_name="deepseek",
    use_checkpoint=True,  # 👈 启用 checkpoint
    checkpoint_db="data/checkpoints/dm.db"
)
```

## 使用方式

### 默认模式（无需修改代码）

```python
# 现有代码完全不需要修改
dm_agent = DMAgentLangChain()

async for event in dm_agent.process_turn(
    session_id="session_123",
    player_action="我把金币扔进柜子",
    game_state=game_state
):
    # ... 处理事件
```

**特点**:
- ✅ 对话历史保存到 `game_state.log`
- ✅ 与存档系统完全集成
- ✅ 无需额外配置
- ✅ 已验证可行

### Checkpoint 模式（需要 async with）

```python
# 需要使用 async with 管理生命周期
async with AsyncSqliteSaver.from_conn_string("data/checkpoints/dm.db") as checkpointer:
    dm_agent = DMAgentLangChain(
        use_checkpoint=True
    )
    dm_agent.checkpointer = checkpointer  # 手动设置

    async for event in dm_agent.process_turn(
        session_id="session_123",
        player_action="我把金币扔进柜子",
        game_state=game_state  # 仍需传入，用于工具调用
    ):
        # ... 处理事件
```

**特点**:
- ✅ 对话历史自动保存到 SQLite
- ✅ 无需手动构建消息历史
- ⚠️ 需要管理 checkpoint 连接
- ⚠️ 与存档系统分离

## 日志输出变化

### 默认模式

```
================================================================================
🎮 DM Agent 初始化完成
📦 使用模型: deepseek/deepseek-v3.1-terminus
🔧 加载工具数量: 15
💾 记忆模式: game_state.log (默认)
================================================================================
```

### Checkpoint 模式

```
================================================================================
🎮 DM Agent 初始化完成
📦 使用模型: deepseek/deepseek-v3.1-terminus
🔧 加载工具数量: 15
✅ Checkpoint 模式已启用: data/checkpoints/dm.db
💾 记忆模式: LangGraph Checkpoint
================================================================================
```

## 兼容性

### 向后兼容 ✅

所有现有代码无需修改：

```python
# 这些代码仍然有效
dm = DMAgentLangChain()
dm = DMAgentLangChain(model_name="deepseek")
dm = DMAgentLangChain(model_name="claude-sonnet")
```

### 新功能（可选）

```python
# 新功能：启用 Checkpoint
dm = DMAgentLangChain(use_checkpoint=True)
```

## 依赖要求

### 默认模式

- `langchain`
- `langchain-openai`
- `langgraph`

### Checkpoint 模式（额外需要）

```bash
uv pip install langgraph-checkpoint-sqlite aiosqlite
```

如果缺少依赖，会自动降级到默认模式并显示警告：

```
⚠️  Checkpoint 模式已请求，但 langgraph-checkpoint-sqlite 未安装
   将使用默认模式（game_state.log）
```

## 性能对比

| 特性 | 默认模式 | Checkpoint 模式 |
|------|---------|---------------|
| 启动速度 | 快 ⚡ | 中等（需要连接数据库） |
| 内存使用 | 低 | 中等 |
| 磁盘I/O | 低（只在存档时写入） | 高（每回合写入） |
| 存档大小 | 小 | 中等（额外的 checkpoint.db） |

## 推荐使用场景

### 使用默认模式的情况：

1. ✅ **单人跑团游戏**（当前项目）
2. ✅ **需要完整存档**
3. ✅ **系统简单可靠优先**
4. ✅ **性能敏感**

### 使用 Checkpoint 模式的情况：

1. ✅ **开发和调试**（方便查看对话历史）
2. ✅ **需要时间旅行**（回到之前的状态）
3. ✅ **多人在线游戏**（未来扩展）
4. ✅ **实验新功能**

## 迁移指南

### 从默认模式迁移到 Checkpoint 模式

**步骤1**: 安装依赖

```bash
uv pip install langgraph-checkpoint-sqlite aiosqlite
```

**步骤2**: 修改初始化代码

```python
# 之前
dm_agent = DMAgentLangChain()

# 之后
async with AsyncSqliteSaver.from_conn_string("data/checkpoints/dm.db") as checkpointer:
    dm_agent = DMAgentLangChain(use_checkpoint=True)
    dm_agent.checkpointer = checkpointer

    # 使用 dm_agent
    async for event in dm_agent.process_turn(...):
        ...
```

**步骤3**: （可选）数据迁移

```python
# 将 game_state.log 导入到 Checkpoint
async def migrate_log_to_checkpoint(game_state, session_id):
    async with AsyncSqliteSaver.from_conn_string("data/checkpoints/dm.db") as checkpointer:
        dm_agent = DMAgentLangChain(use_checkpoint=True)
        dm_agent.checkpointer = checkpointer

        # 重放历史
        for entry in game_state['log']:
            if entry['actor'] == 'player':
                await dm_agent.process_turn(
                    session_id=session_id,
                    player_action=entry['text'],
                    game_state=game_state
                )
```

## 故障排除

### 问题1: "Checkpoint 模式未启用"

**症状**:
```
⚠️  LangGraph Checkpoint 未安装，使用默认模式
```

**解决方案**:
```bash
uv pip install langgraph-checkpoint-sqlite aiosqlite
```

### 问题2: "AttributeError: 'NoneType' object has no attribute 'aget'"

**原因**: Checkpoint 模式下忘记设置 `checkpointer`

**解决方案**:
```python
async with AsyncSqliteSaver.from_conn_string(...) as checkpointer:
    dm_agent = DMAgentLangChain(use_checkpoint=True)
    dm_agent.checkpointer = checkpointer  # 👈 不要忘记这一行
```

### 问题3: "RuntimeError: Event loop is closed"

**原因**: Checkpoint 连接未正确关闭

**解决方案**: 使用 `async with` 管理生命周期

```python
# 正确
async with AsyncSqliteSaver.from_conn_string(...) as checkpointer:
    # 使用 checkpointer
    pass

# 错误
checkpointer = AsyncSqliteSaver.from_conn_string(...)  # ❌ 没有 async with
```

## 测试

### 测试默认模式

```bash
uv run python tests/integration/test_dm_memory.py
```

### 测试 Checkpoint 模式

```bash
uv run python tests/integration/test_checkpoint_simple.py
```

## 文档

- 对话历史修复：`docs/troubleshooting/CONVERSATION_HISTORY_FIX.md`
- Checkpoint 集成分析：`docs/troubleshooting/LANGGRAPH_CHECKPOINT_INTEGRATION.md`
- Checkpoint 测试报告：`docs/troubleshooting/LANGGRAPH_CHECKPOINT_SUCCESS.md`
- 长期记忆完整方案：`docs/troubleshooting/LANGGRAPH_MEMORY_FINAL.md`

## 总结

### 核心变化

1. **新增可选参数**: `use_checkpoint` 和 `checkpoint_db`
2. **向后兼容**: 现有代码无需修改
3. **双模式支持**: 默认模式 + Checkpoint 模式

### 推荐策略

1. **生产环境**: 继续使用默认模式
2. **开发调试**: 可选使用 Checkpoint 模式
3. **未来迁移**: 清晰的迁移路径

### 下一步

- [ ] 添加混合模式（同时使用两者）
- [ ] 实现自动数据同步
- [ ] 添加 Checkpoint 快照功能
- [ ] 性能优化和基准测试
