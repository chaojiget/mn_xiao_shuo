# 流式聊天功能 - 快速总结

## ✨ 已实现功能

### 1. 聊天页面
- **路径**: http://localhost:3000/chat
- **设计**: ChatGPT 风格,每条消息一个气泡
- **流式输出**: 实时显示 AI 生成的文本
- **特性**:
  - 用户消息:蓝色渐变,右对齐
  - AI 消息:半透明白色,左对齐
  - 流式输出时显示闪烁光标
  - Enter 发送,Shift+Enter 换行
  - 自动滚动到最新消息

### 2. 后端 API
- **端点**: `POST /api/chat/stream`
- **格式**: Server-Sent Events (SSE)
- **当前状态**: 模拟流式响应(演示用)

## 🚀 使用方法

1. 访问 http://localhost:3000
2. 点击右上角"聊天模式"按钮
3. 输入消息并发送
4. 观看 AI 实时生成回复

## 🔧 集成真实 AI

### 方式一: 使用 LiteLLM (已集成)

修改 `web/backend/chat_api.py`:

```python
from pathlib import Path
from src.llm import LiteLLMClient

async def generate_stream_response(message: str):
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config" / "litellm_config.yaml"

    llm_client = LiteLLMClient(config_path=str(config_path))

    # LiteLLM 流式生成
    full_response = await llm_client.generate(
        prompt=message,
        model="deepseek",
        max_tokens=2000,
        temperature=0.8
    )

    # 逐字输出
    for char in full_response:
        data = {"type": "text", "content": char}
        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
```

### 方式二: 使用 Claude Agent SDK

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

async def generate_stream_response(message: str):
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash"],
        max_turns=1
    )

    async for msg in query(prompt=message, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    data = {"type": "text", "content": block.text}
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
```

### 方式三: 使用 Vercel AI SDK (推荐)

基于 Vercel AI Chatbot 的最佳实践:

```typescript
// 前端使用 useChat hook
import { useChat } from "@ai-sdk/react"

const { messages, sendMessage, status } = useChat({
  api: "/api/chat/stream"
})
```

```python
# 后端使用 streamText
from ai import streamText

async def generate_stream_response(message: str):
    result = await streamText({
        "model": "deepseek",
        "messages": [{"role": "user", "content": message}]
    })

    # 流式输出
    async for chunk in result.textStream:
        data = {"type": "text-delta", "textDelta": chunk}
        yield f"data: {json.dumps(data)}\n\n"

    yield f"data: [DONE]\n\n"
```

## 📁 相关文件

```
web/
├── backend/
│   ├── main.py              # FastAPI 主应用(已注册路由)
│   └── chat_api.py          # 聊天 API(流式端点)
└── frontend/
    └── app/
        ├── page.tsx         # 主页(有"聊天模式"按钮)
        └── chat/
            └── page.tsx     # 聊天页面(已修复)
```

## 🐛 已修复问题

1. **消息索引错误**: 修改为使用 `messages.length - 1`
2. **内容累加**: 使用局部变量 `assistantContent` 累加
3. **CORS 配置**: 后端已配置允许 localhost:3000

## 📝 数据流

```
用户输入
  ↓
前端发送 POST /api/chat/stream
  ↓
后端生成流式响应 (SSE)
  ↓
data: {"type": "text", "content": "你"}
data: {"type": "text", "content": "好"}
...
data: {"type": "done"}
  ↓
前端实时更新 UI
  ↓
显示完整消息
```

## 🎯 下一步

1. ✅ 基础聊天界面
2. ✅ 流式输出显示
3. ⏳ 连接真实 AI (3种方式可选)
4. ⏳ 对话历史持久化
5. ⏳ 多轮对话上下文

## 💡 提示

- 当前使用模拟数据,部署时替换 `chat_api.py` 中的 `generate_stream_response` 函数
- 推荐使用已集成的 LiteLLM + DeepSeek V3 模型
- 参考 Vercel AI Chatbot 的 `useChat` hook 可以简化前端代码
