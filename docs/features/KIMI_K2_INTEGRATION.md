# Kimi K2 Thinking 模型集成指南

## 概述

本文档说明如何将 Moonshot AI 的 Kimi K2 Thinking 模型集成到系统中，以及如何利用其思考过程可视化功能。

## 模型切换

### 方法 1: 修改环境变量（推荐）

编辑 `.env` 文件：

```bash
# 默认模型
DEFAULT_MODEL=moonshotai/kimi-k2-thinking
```

### 方法 2: 代码中指定

```python
from agents.dm_agent_langchain import DMAgentLangChain

# 使用完整名称
dm_agent = DMAgentLangChain(model_name="moonshotai/kimi-k2-thinking")

# 或使用简写
dm_agent = DMAgentLangChain(model_name="kimi")
```

### 方法 3: 模型映射

系统已预配置以下模型映射：

```python
model_map = {
    "deepseek": "deepseek/deepseek-v3.1-terminus",
    "claude-sonnet": "anthropic/claude-3.5-sonnet",
    "claude-haiku": "anthropic/claude-3-haiku",
    "gpt-4": "openai/gpt-4-turbo",
    "qwen": "qwen/qwen-2.5-72b-instruct",
    "kimi": "moonshotai/kimi-k2-thinking"  # 新增
}
```

## Kimi K2 Thinking 特性

### 1. 思考链展示

Kimi K2 Thinking 是一个推理增强模型，会在生成最终答案前展示思考过程。

**思考过程标记:**
```
<thinking>
推理步骤1: 分析问题...
推理步骤2: 评估选项...
推理步骤3: 得出结论...
</thinking>

最终答案：...
```

### 2. 自动检测

后端会自动检测以下标记并转换为 UI 事件：

- `<thinking>` → `thinking_start` 事件
- 思考内容 → `thinking_step` 事件
- `</thinking>` → `thinking_end` 事件
- 其他标记：`思考：`、`<think>`、`推理：`、`分析：`

### 3. UI 可视化

前端会自动渲染思考过程：

```tsx
{/* 思考过程自动展示 */}
<ThinkingProcess steps={thinkingSteps} isThinking={isThinking} />
```

**效果:**
```
┌─────────────────────────────────────┐
│ 🧠 AI 思考过程            ▼   3 步 │
├─────────────────────────────────────┤
│ ① 分析玩家意图                      │
│   根据输入判断...                   │
│                                     │
│ ② 评估可用工具                      │
│   需要调用 get_player_state...      │
│                                     │
│ ③ 规划响应策略                      │
│   先描述场景，再调用工具...         │
└─────────────────────────────────────┘
```

## 完整工作流程

### 1. 用户输入

```
玩家: "我想探索这个洞穴"
```

### 2. Kimi K2 思考过程（后台）

```xml
<thinking>
分析1: 玩家想要探索洞穴，这是一个探索行动
分析2: 需要检查玩家当前状态和位置
分析3: 应该调用 get_player_state 获取信息
分析4: 然后描述洞穴场景，调用 roll_check 进行探索检定
</thinking>
```

### 3. 前端展示

**思考过程卡片:**
```
🧠 AI 思考过程
├─ ① 分析玩家意图
│    玩家想要探索洞穴，这是一个探索行动
├─ ② 检查游戏状态
│    需要检查玩家当前状态和位置
├─ ③ 规划工具调用
│    应该调用 get_player_state 获取信息
└─ ④ 设计响应策略
     然后描述洞穴场景，调用 roll_check 进行探索检定
```

**任务进度:**
```
AI 工作进度                2/2
━━━━━━━━━━━━━━━━━━━━━━━

✓ 工具调用: get_player_state
✓ 工具调用: roll_check
```

**AI 建议:**
```
🗺️ 探索洞穴深处  ⚔️ 准备战斗  ❓ 仔细观察环境
```

### 4. 最终输出

```
你小心翼翼地走进洞穴。潮湿的空气中弥漫着霉味，
远处传来滴水声。你的眼睛逐渐适应黑暗...

（检定成功！你发现了一条隐藏的通道）
```

## 性能对比

| 模型 | 速度 | 推理能力 | 中文质量 | 成本 |
|------|------|----------|----------|------|
| DeepSeek V3 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $ |
| Kimi K2 Thinking | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $$ |
| Claude 3.5 Sonnet | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$$ |
| GPT-4 Turbo | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$$ |

## 使用建议

### 适合使用 Kimi K2 的场景

1. **复杂推理任务**
   - 多步骤推理
   - 需要展示思考过程
   - 教育/演示场景

2. **调试和理解**
   - 理解 AI 决策过程
   - 调试工具调用逻辑
   - 优化提示词

3. **高质量生成**
   - 需要深度思考的创作
   - 复杂剧情设计
   - 逻辑严密的对话

### 不建议使用的场景

1. **简单问答**
   - 基础信息查询
   - 快速响应需求
   → 推荐使用 DeepSeek V3 或 Claude Haiku

2. **大量生成**
   - 批量章节生成
   - 成本敏感场景
   → 推荐使用 DeepSeek V3

## 高级配置

### 自定义思考过程检测

修改 `dm_agent_langchain.py:350-373`：

```python
# 自定义思考标记
custom_markers = [
    "<thinking>",
    "思考：",
    "推理：",
    "分析：",
    "我的思路：",  # 新增
    "让我想想：",  # 新增
]

if any(marker in content for marker in custom_markers):
    yield {
        "type": "thinking_step",
        "content": content
    }
```

### 思考过程样式自定义

修改 `ThinkingProcess.tsx`：

```tsx
// 自定义颜色主题
const themeColors = {
  background: 'from-purple-50 to-blue-50',
  darkBackground: 'dark:from-purple-950/20 dark:to-blue-950/20',
  header: 'bg-purple-100/50',
  icon: 'text-purple-600',
};
```

## 故障排除

### 问题 1: 思考过程未显示

**检查清单:**
1. ✅ 确认使用的是 Kimi K2 模型
2. ✅ 检查后端日志是否有 `thinking_step` 事件
3. ✅ 确认前端组件已正确集成

**解决方法:**
```bash
# 查看后端日志
cd web/backend
uv run uvicorn main:app --reload --log-level debug

# 查看前端控制台
# 打开浏览器开发者工具，检查 WebSocket 或 SSE 消息
```

### 问题 2: 思考过程格式混乱

**原因:** Kimi K2 的输出格式可能变化

**解决方法:**
调整检测逻辑以适应新格式：

```python
# 更宽松的检测
if "思考" in content or "推理" in content or "分析" in content:
    yield {"type": "thinking_step", "content": content}
```

### 问题 3: 性能较慢

**原因:** Kimi K2 需要额外时间进行推理

**解决方法:**
1. 启用流式输出（已默认启用）
2. 显示加载动画和思考过程
3. 对于简单任务使用 DeepSeek V3

## 示例代码

### 完整的 Kimi K2 集成示例

```python
# backend/main.py
from agents.dm_agent_langchain import DMAgentLangChain

# 初始化 Kimi K2 Agent
dm_agent = DMAgentLangChain(
    model_name="kimi",
    use_checkpoint=True,
    checkpoint_db="data/checkpoints/kimi.db"
)

# 处理用户输入
async for event in dm_agent.process_turn(
    session_id="user123",
    player_action="探索洞穴",
    game_state=current_state
):
    if event["type"] == "thinking_step":
        print(f"思考: {event['content']}")
    elif event["type"] == "narration":
        print(f"叙事: {event['content']}")
    elif event["type"] == "tool_call":
        print(f"工具: {event['tool']}")
```

```tsx
// frontend/components/game/DmInterface.tsx
const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
const [isThinking, setIsThinking] = useState(false);

// 处理流式消息
if (data.type === 'thinking_step') {
  const newStep: ThinkingStep = {
    id: `think_${Date.now()}`,
    title: `思考步骤 ${thinkingSteps.length + 1}`,
    content: data.content,
    status: 'completed',
    timestamp: Date.now(),
  };
  setThinkingSteps((prev) => [...prev, newStep]);
}

// 渲染思考过程
<ThinkingProcess steps={thinkingSteps} isThinking={isThinking} />
```

## 相关文档

- [AI 思考过程可视化 UI](./AI_THINKING_UI.md)
- [LangChain 1.0 迁移](../implementation/LANGCHAIN_MIGRATION_PLAN.md)
- [CLAUDE.md](/CLAUDE.md) - 项目总览
- [OpenRouter 配置指南](../guides/OPENROUTER_SETUP.md)

## 更新日志

- **2025-11-08**: 添加 Kimi K2 Thinking 模型支持
- **2025-11-08**: 实现思考过程可视化 UI
- **2025-11-08**: 添加 AI 建议芯片和任务进度组件
