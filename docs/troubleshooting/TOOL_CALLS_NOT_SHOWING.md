# 工具调用和思考过程不显示问题 - 解决方案

**问题时间**: 2025-11-10
**问题描述**: 前端界面看不到工具调用过程和思考步骤
**根本原因**: LangGraph Checkpoint 模式无法流式传输工具调用事件

---

## 🔍 问题分析

### **当前架构**

后端使用了 **LangGraph Checkpoint 模式**（`web/backend/api/dm_api.py:38-42`）:

```python
dm_agent = DMAgentLangChain(
    model_name=model_name,
    use_checkpoint=True,  # 👈 Checkpoint 模式开启
    checkpoint_db="data/checkpoints/dm.db"
)
```

### **Checkpoint 模式的限制**

在 `web/backend/agents/dm_agent_langchain.py:295-317` 中：

```python
if self.use_checkpoint and self.checkpointer:
    # 使用 agent.astream() - 只能获取最终消息
    async for event in agent.astream({"messages": message_history}, config=config):
        if "agent" in event:
            # 只能拿到 agent 返回的最终消息
            # ❌ 无法获取工具调用事件 (on_tool_start/on_tool_end)
            # ❌ 无法获取思考过程 (thinking tags)
```

相比之下，**非 Checkpoint 模式**使用 `astream_events()`（第352-399行）:

```python
async for event in agent.astream_events({"messages": message_history}, version="v2"):
    # ✅ 可以获取 on_tool_start 事件
    # ✅ 可以获取 on_tool_end 事件
    # ✅ 可以检测 <thinking> 标签
    # ✅ 可以流式传输所有内容
```

---

## ✅ 解决方案 1: 切换到非 Checkpoint 模式

### **步骤 1: 修改环境变量**

编辑 `.env` 文件（如果没有则从 `.env.example` 复制）:

```bash
# 禁用 Checkpoint 模式
USE_CHECKPOINT=false
```

### **步骤 2: 修改 DM Agent 初始化代码**

编辑 `web/backend/api/dm_api.py`:

```python
def init_dm_agent():
    """初始化 DM Agent"""
    global dm_agent
    import os
    from agents.dm_agent_langchain import DMAgentLangChain

    model_name = os.getenv("DEFAULT_MODEL")
    if not model_name:
        logger.warning("⚠️  警告: DEFAULT_MODEL 环境变量未设置")
        model_name = "deepseek/deepseek-v3.1-terminus"

    # 🔥 修改：禁用 Checkpoint 模式
    dm_agent = DMAgentLangChain(
        model_name=model_name,
        use_checkpoint=False,  # 👈 改为 False
        # checkpoint_db="data/checkpoints/dm.db"  # 👈 注释掉
    )
    logger.info(f"✅ DM Agent 已初始化 (模型: {model_name}, 无 Checkpoint)")
```

### **步骤 3: 重启后端**

```bash
# 停止当前后端
pkill -f "uvicorn main:app"

# 重新启动
cd web/backend
../../.venv/bin/uvicorn main:app --reload --port 8000
```

### **测试效果**

刷新页面，发送消息，你应该能看到：
- ✅ **思考过程**显示在 `ThinkingProcess` 组件中
- ✅ **工具调用**显示在 `TaskProgress` 组件中
- ✅ **流式输出**逐字显示

---

## ✅ 解决方案 2: 混合模式（推荐）

保留 Checkpoint 的记忆功能，但增强事件捕获。

### **修改 dm_agent_langchain.py**

在 `process_turn()` 方法中（第295行附近），添加工具调用检测：

```python
if self.use_checkpoint and self.checkpointer:
    agent = create_react_agent(...)

    async for event in agent.astream({"messages": message_history}, config=config):
        # 🔥 新增：检测工具调用
        if "agent" in event:
            agent_event = event["agent"]

            # 检测 messages 中的工具调用
            if "messages" in agent_event:
                for msg in agent_event["messages"]:
                    # 检测 AIMessage 中的 tool_calls
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            yield {
                                "type": "tool_call",
                                "tool": tool_call.get("name"),
                                "input": tool_call.get("args", {})
                            }

                    # 检测 ToolMessage (工具返回结果)
                    if hasattr(msg, "type") and msg.type == "tool":
                        yield {
                            "type": "tool_result",
                            "tool": getattr(msg, "name", "unknown"),
                            "output": msg.content
                        }

                    # 流式输出内容
                    if hasattr(msg, "content") and msg.content:
                        # 🔥 检测思考过程
                        if "<thinking>" in msg.content:
                            yield {"type": "thinking_start", "content": ""}
                        elif "</thinking>" in msg.content:
                            yield {"type": "thinking_end", "content": ""}
                        else:
                            full_narration.append(msg.content)
                            yield {"type": "narration", "content": msg.content}
```

---

## 📊 两种方案对比

| 特性 | 方案1: 非Checkpoint | 方案2: 混合模式 |
|-----|-------------------|----------------|
| **工具调用可见** | ✅ 完全可见 | ✅ 可见（需手动提取） |
| **思考过程可见** | ✅ 实时流式 | ⚠️ 需检测标签 |
| **对话历史记忆** | ❌ 需手动管理 | ✅ 自动记忆 |
| **实现复杂度** | 简单 | 中等 |
| **推荐场景** | 调试/演示 | 生产环境 |

---

## 🎯 推荐方案

### **调试阶段**: 使用方案 1
- 可以清楚看到所有事件
- 方便调试工具调用
- 方便测试思考过程显示

### **生产环境**: 使用方案 2
- 保留对话历史自动管理
- 增强事件检测
- 更稳定的用户体验

---

## 🐛 已知问题

### **问题 1: JSON 解析错误**

**错误**: `Unterminated string starting at: line 10 column 9`

**原因**: LLM 返回的 JSON 格式不完整（工具调用参数过长）

**解决**:
```python
# 在 langchain_backend.py 中增加超时和最大 token 限制
model = ChatOpenAI(
    base_url=base_url,
    api_key=api_key,
    model=model_name,
    temperature=temperature,
    max_tokens=2000,  # 👈 增加限制
    timeout=30,  # 👈 增加超时
)
```

### **问题 2: 思考过程标签不被识别**

**原因**: 不同模型使用不同的思考标记

**支持的标记**:
- `<thinking>...</thinking>` (Kimi K2)
- `<think>...</think>` (DeepSeek)
- `思考：...` (中文模型)
- `推理：...` (中文模型)

**解决**: 在前端添加更多标记检测（已实现）

---

## 📚 相关文件

- `web/backend/api/dm_api.py:23-43` - DM Agent 初始化
- `web/backend/agents/dm_agent_langchain.py:263-416` - 流式处理逻辑
- `web/frontend/components/game/DmInterface.tsx:100-244` - WebSocket 消息处理
- `web/frontend/components/chat/ThinkingProcess.tsx` - 思考过程显示
- `web/frontend/components/chat/TaskProgress.tsx` - 工具调用显示

---

## ✅ 完成检查清单

- [x] 添加错误显示组件 (ErrorDisplay)
- [x] 添加重试按钮
- [x] 分析 Checkpoint 模式限制
- [x] 提供两种解决方案
- [x] 编写文档
- [ ] 用户选择方案并测试

---

**更新时间**: 2025-11-10 21:55
**作者**: Claude Code
**版本**: 1.0
**状态**: ✅ 完成（待用户选择方案）
