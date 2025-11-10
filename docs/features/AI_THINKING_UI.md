# AI 思考过程可视化 UI

## 概述

本系统现已支持展示 AI 的思考过程和任务进度，类似于 Claude Artifacts 和 ChatGPT 的建议芯片功能。这为用户提供了更透明的 AI 交互体验。

## 新增功能

### 1. 思考过程展示 (ThinkingProcess)

**功能描述:**
- 实时展示 AI 的推理步骤（特别适配 Kimi K2 Thinking 模型）
- 可折叠的思考链展示
- 每个思考步骤带有时间戳和状态标识

**组件位置:** `web/frontend/components/chat/ThinkingProcess.tsx`

**使用示例:**
```tsx
import { ThinkingProcess, ThinkingStep } from '@/components/chat/ThinkingProcess';

const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
const [isThinking, setIsThinking] = useState(false);

// 添加思考步骤
const addThinkingStep = (content: string) => {
  const newStep: ThinkingStep = {
    id: `think_${Date.now()}`,
    title: `思考步骤 ${thinkingSteps.length + 1}`,
    content: content,
    status: 'completed',
    timestamp: Date.now(),
  };
  setThinkingSteps((prev) => [...prev, newStep]);
};

<ThinkingProcess steps={thinkingSteps} isThinking={isThinking} />
```

**思考步骤状态:**
- `thinking`: 正在思考（蓝色，带动画）
- `completed`: 已完成（绿色）
- `pending`: 待处理（灰色）

### 2. AI 建议芯片 (SuggestionChips)

**功能描述:**
- 提供智能化的后续行动建议
- 可点击直接填充到输入框
- 支持多种建议类型（探索、行动、问题、创意）

**组件位置:** `web/frontend/components/chat/SuggestionChips.tsx`

**使用示例:**
```tsx
import { SuggestionChips, Suggestion } from '@/components/chat/SuggestionChips';

const [suggestions, setSuggestions] = useState<Suggestion[]>([
  {
    id: 'explore',
    text: '探索周围环境',
    category: 'explore',
  },
  {
    id: 'talk',
    text: '与 NPC 对话',
    category: 'question',
  },
  {
    id: 'search',
    text: '搜索线索',
    category: 'action',
  },
]);

const handleSuggestionClick = (suggestion: Suggestion) => {
  setInput(suggestion.text);
};

<SuggestionChips
  suggestions={suggestions}
  onSelect={handleSuggestionClick}
  onRefresh={generateSuggestions}
/>
```

**建议类型:**
- `explore` 🗺️: 探索类（蓝色）
- `action` ⚔️: 行动类（红色）
- `question` ❓: 问题类（紫色）
- `creative` ✨: 创意类（绿色）

### 3. 任务进度列表 (TaskProgress)

**功能描述:**
- 展示 AI 工作进度（类似 Claude Artifacts）
- 支持文件引用和代码标识
- 实时更新任务状态
- 带进度条显示整体完成度

**组件位置:** `web/frontend/components/chat/TaskProgress.tsx`

**使用示例:**
```tsx
import { TaskProgress, Task } from '@/components/chat/TaskProgress';

const [tasks, setTasks] = useState<Task[]>([]);

// 添加新任务
const addTask = (title: string) => {
  const newTask: Task = {
    id: `task_${Date.now()}`,
    title: title,
    status: 'in_progress',
    type: 'code',
    timestamp: Date.now(),
  };
  setTasks((prev) => [...prev, newTask]);
};

// 更新任务状态
const completeTask = (taskId: string) => {
  setTasks((prev) =>
    prev.map((task) =>
      task.id === taskId
        ? { ...task, status: 'completed' as const }
        : task
    )
  );
};

<TaskProgress tasks={tasks} title="AI 工作进度" />
```

**任务状态:**
- `pending`: 待处理（灰色）
- `in_progress`: 进行中（蓝色，带动画）
- `completed`: 已完成（绿色，带勾选）
- `error`: 错误（红色）

**任务类型:**
- `file` 📄: 文件操作
- `code` 💻: 代码生成
- `text` 📝: 文本处理
- `other` ⭕: 其他任务

## 后端支持

### 修改的文件

1. **`web/backend/agents/dm_agent_langchain.py`**
   - 添加思考过程检测逻辑
   - 识别 Kimi K2 Thinking 模型的特殊标记

2. **`web/backend/api/dm_api.py`**
   - 支持流式输出思考步骤

### 事件类型

后端现在支持以下事件类型：

```python
# 思考过程
{
  "type": "thinking_start",
  "content": ""
}

{
  "type": "thinking_step",
  "content": "推理内容..."
}

{
  "type": "thinking_end",
  "content": ""
}

# 叙事内容
{
  "type": "narration",
  "content": "场景描述..."
}

# 工具调用
{
  "type": "tool_call",
  "tool": "工具名称",
  "input": {...}
}

{
  "type": "tool_result",
  "tool": "工具名称",
  "output": {...}
}
```

## 完整集成示例

在 `DmInterface.tsx` 中的完整集成：

```tsx
export function DmInterface({ sessionId, className }: DmInterfaceProps) {
  // 状态管理
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);

  // 处理 WebSocket 或 HTTP 流式消息
  const handleMessage = (data: any) => {
    switch (data.type) {
      case 'thinking_start':
        setIsThinking(true);
        break;

      case 'thinking_step':
        const newStep: ThinkingStep = {
          id: `think_${Date.now()}`,
          title: `思考步骤 ${thinkingSteps.length + 1}`,
          content: data.content,
          status: 'completed',
          timestamp: Date.now(),
        };
        setThinkingSteps((prev) => [...prev, newStep]);
        break;

      case 'thinking_end':
        setIsThinking(false);
        break;

      case 'tool_call':
        const newTask: Task = {
          id: `task_${Date.now()}`,
          title: `工具调用: ${data.tool}`,
          status: 'in_progress',
          type: 'code',
          timestamp: Date.now(),
        };
        setTasks((prev) => [...prev, newTask]);
        break;

      case 'tool_result':
        setTasks((prev) =>
          prev.map((task) =>
            task.status === 'in_progress'
              ? { ...task, status: 'completed' as const }
              : task
          )
        );
        break;
    }
  };

  return (
    <div>
      {/* 思考过程展示 */}
      {(thinkingSteps.length > 0 || isThinking) && (
        <ThinkingProcess steps={thinkingSteps} isThinking={isThinking} />
      )}

      {/* 任务进度展示 */}
      {tasks.length > 0 && <TaskProgress tasks={tasks} />}

      {/* AI 建议芯片 */}
      {suggestions.length > 0 && (
        <SuggestionChips
          suggestions={suggestions}
          onSelect={handleSuggestionClick}
          onRefresh={generateSuggestions}
        />
      )}
    </div>
  );
}
```

## 模型配置

### 使用 Kimi K2 Thinking

在 `.env` 文件中配置：

```bash
DEFAULT_MODEL=moonshotai/kimi-k2-thinking
```

或在代码中使用简写：

```python
from agents.dm_agent_langchain import DMAgentLangChain

dm_agent = DMAgentLangChain(model_name="kimi")
```

### 思考过程检测

系统会自动检测以下标记：

- `<thinking>` / `</thinking>`: 思考块开始/结束
- `思考：`: 中文思考标记
- `<think>`: 思考步骤
- `推理：`: 推理步骤
- `分析：`: 分析步骤

## 样式和主题

所有组件都支持亮色/暗色主题，使用 Tailwind CSS 的 dark mode：

```tsx
// 亮色模式
bg-purple-50 text-purple-700

// 暗色模式
dark:bg-purple-950/20 dark:text-purple-300
```

## 最佳实践

1. **思考过程展示**
   - 只在使用推理模型（如 Kimi K2 Thinking）时启用
   - 保持思考步骤简洁明了
   - 允许用户折叠/展开

2. **AI 建议**
   - 提供 2-4 个建议最佳
   - 建议应该具体且可操作
   - 根据上下文动态生成

3. **任务进度**
   - 及时更新任务状态
   - 提供有意义的任务描述
   - 错误时显示错误信息

## 技术栈

- **前端框架**: Next.js 14 + TypeScript
- **UI 组件**: shadcn/ui (基于 Radix UI)
- **样式**: Tailwind CSS
- **图标**: Lucide React
- **后端**: FastAPI + LangChain 1.0
- **AI 模型**: Kimi K2 Thinking (via OpenRouter)

## 相关文档

- [CLAUDE.md](/CLAUDE.md) - 项目总览
- [世界脚手架指南](./WORLD_SCAFFOLD_GUIDE.md)
- [快速开始指南](../guides/QUICK_START.md)
- [LangChain 迁移计划](../implementation/LANGCHAIN_MIGRATION_PLAN.md)
