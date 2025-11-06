# 对话记录缓存修复

## 问题描述

**症状**：DM 在对话中"失忆"，无法记住之前说过的话（如柜子里的物品消失）

**根本原因**：DM Agent 处理完回合后，**没有将对话保存到游戏日志** (`game_state.log`)

## 问题分析

### 原有流程

```
用户输入 → DM Agent 处理 → 生成回复 → ❌ 没有保存到日志
                                      ↓
                                   下次对话时，DM看不到之前的回复
```

### 代码层面

#### 问题1：流式处理 (`process_turn`)

```python
# 原来的代码
async for event in agent.astream_events(...):
    if event_type == "on_chat_model_stream":
        chunk = chunk.content
        yield {"type": "narration", "content": chunk}
        # ❌ 文本流式发送后就丢失了，没有保存

# 结果：完整的叙事文本没有被保存到 game_state.log
```

#### 问题2：非流式处理 (`process_turn_sync`)

```python
# 原来的代码
narration = "\n\n".join(narration_parts)
return {
    "narration": narration,
    # ❌ 没有保存到 game_state.log
}
```

## 修复方案

### 1. 新增 `_save_to_log` 方法

```python
def _save_to_log(self, game_state: Dict[str, Any], player_action: str, dm_response: str):
    """保存对话到游戏日志

    Args:
        game_state: 游戏状态
        player_action: 玩家行动
        dm_response: DM回复
    """
    import time

    # 确保 log 列表存在
    if 'log' not in game_state:
        game_state['log'] = []

    # 添加玩家行动
    game_state['log'].append({
        "actor": "player",
        "text": player_action,
        "timestamp": int(time.time())
    })

    # 添加DM回复
    if dm_response and dm_response.strip():
        game_state['log'].append({
            "actor": "dm",
            "text": dm_response,
            "timestamp": int(time.time())
        })

    logger.debug(f"📝 已保存到日志: 玩家输入 + DM回复 (共 {len(game_state['log'])} 条)")
```

### 2. 修复流式处理

```python
async def process_turn(self, ...):
    # 🔥 收集完整的叙事文本
    full_narration = []

    async for event in agent.astream_events(...):
        if event_type == "on_chat_model_stream":
            chunk = chunk.content
            full_narration.append(chunk)  # 🔥 收集文本
            yield {"type": "narration", "content": chunk}

    # 🔥 保存到日志
    self._save_to_log(game_state, player_action, "".join(full_narration))
```

### 3. 修复非流式处理

```python
async def process_turn_sync(self, ...):
    narration_parts = []
    # ... 收集 narration_parts

    # 🔥 保存到日志
    full_narration = "\n\n".join(narration_parts)
    self._save_to_log(game_state, player_action, full_narration)

    return {
        "narration": full_narration,
        ...
    }
```

## 修复后的流程

```
用户输入 → DM Agent 处理 → 生成回复 → ✅ 保存到 game_state.log
                                      ↓
                                   [{"actor": "player", "text": "..."},
                                    {"actor": "dm", "text": "..."}]
                                      ↓
                                   下次对话时，DM可以看到完整历史
```

## 数据结构

### game_state.log 格式

```python
[
    {
        "actor": "player",
        "text": "我扔掉金币",
        "timestamp": 1699200000
    },
    {
        "actor": "dm",
        "text": "你把金币扔进通风管道...柜子里隐约反射着金属的光泽。",
        "timestamp": 1699200001
    },
    {
        "actor": "player",
        "text": "我往前走",
        "timestamp": 1699200010
    },
    {
        "actor": "dm",
        "text": "你缓缓往前走，刚才那个柜子里的金属光泽依然吸引着你的注意...",
        "timestamp": 1699200011
    }
]
```

### 消息历史构建 (`_build_message_history`)

```python
# 从 game_state.log 读取历史
log_entries = game_state.get('log', [])

for log_entry in log_entries:
    actor = log_entry.get('actor')
    text = log_entry.get('text')

    if actor == 'player':
        messages.append({"role": "user", "content": f"玩家行动: {text}"})
    elif actor == 'dm':
        messages.append({"role": "assistant", "content": text})

# 添加当前玩家行动
messages.append({"role": "user", "content": f"玩家行动: {current_player_action}"})
```

## 测试验证

### 测试场景

1. **场景1：柜子里的物品**
   - 回合1：DM说"柜子里有金属光泽"
   - 回合2：玩家问"什么？"
   - ✅ DM应该能回忆起"柜子里的金属光泽"

2. **场景2：NPC对话**
   - 回合1：NPC说"我需要你帮我找到钥匙"
   - 回合2：玩家问"你刚才说什么？"
   - ✅ DM应该能回忆起NPC说过的话

### 验证方法

```python
# 在游戏回合后检查日志
print(f"日志条目数: {len(game_state['log'])}")
for entry in game_state['log'][-4:]:  # 最后4条
    print(f"[{entry['actor']}] {entry['text'][:50]}...")
```

**期望输出**：
```
日志条目数: 4
[player] 我扔掉金币
[dm] 你把金币扔进通风管道...柜子里有金属光泽...
[player] 我往前走
[dm] 你缓缓往前走，柜子里的金属光泽依然吸引着你...
```

## 相关修复

本次修复同时解决了之前的另一个问题：

### 之前的修复：添加历史上下文传递

**文件**: `web/backend/agents/dm_agent_langchain.py`

**修改点**:
```python
# 修复前
{"messages": [{"role": "user", "content": user_message}]}  # ❌ 只有当前输入

# 修复后
message_history = self._build_message_history(game_state, player_action)
{"messages": message_history}  # ✅ 完整历史
```

### 两次修复的关系

1. **第一次修复**（之前）：让DM能够**读取**历史对话
2. **第二次修复**（本次）：让DM的回复能够**保存**到历史对话

两者缺一不可！

## 文件清单

### 修改的文件

- `web/backend/agents/dm_agent_langchain.py`
  - 新增 `_save_to_log()` 方法
  - 修改 `process_turn()` 流式方法
  - 修改 `process_turn_sync()` 非流式方法

### 新增的文件

- `docs/troubleshooting/CONVERSATION_HISTORY_FIX.md` (本文档)

## LangChain 1.0 相关参考

### 消息历史管理

LangChain 1.0 中推荐的做法：

```python
from langchain.memory import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

# 创建消息历史
history = ChatMessageHistory()

# 添加消息
history.add_user_message("用户输入")
history.add_ai_message("AI回复")

# 获取消息
messages = history.messages

# 与Agent集成
agent_executor = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt
)

result = await agent_executor.ainvoke({
    "messages": messages  # 传递完整历史
})
```

### 我们的实现 vs LangChain 标准

| 特性 | LangChain 标准 | 我们的实现 | 原因 |
|------|---------------|-----------|------|
| 存储格式 | `ChatMessageHistory` | `game_state.log` (dict) | 需要持久化到数据库 |
| 消息类型 | `HumanMessage`, `AIMessage` | `{"role": "user/assistant"}` | 兼容OpenAI格式 |
| 持久化 | 可选 | 必须 | 游戏需要存档 |
| Session管理 | `ConversationBufferMemory` | 自定义 | 支持多会话 |

### 优势

我们的实现比LangChain标准方案**更适合游戏场景**：

1. ✅ 直接集成到游戏状态中
2. ✅ 自动持久化到数据库
3. ✅ 支持存档和加载
4. ✅ 与游戏引擎无缝集成

## 后续优化建议

### 短期

- [ ] 添加日志条目限制（如最多保留100条）
- [ ] 实现日志摘要功能（压缩旧日志）
- [ ] 添加日志搜索功能

### 长期

- [ ] 实现向量检索（使用Chroma/FAISS）
- [ ] 智能摘要（使用LLM总结旧对话）
- [ ] 多模态记忆（支持图片、音频）

## 相关文档

- [DM上下文修复](./DM_CONTEXT_FIX.md) - 之前的上下文传递修复
- [LangChain迁移](../implementation/LANGCHAIN_MIGRATION_PLAN.md)
- [游戏引擎](../features/GAME_ENGINE.md)
