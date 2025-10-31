# 聊天功能说明

## ✨ 功能特性

### 1. 流式输出
- 使用 Server-Sent Events (SSE) 实现实时流式响应
- 每个字符逐步显示,提供流畅的打字机效果
- 在流式输出过程中显示闪烁的光标指示器

### 2. 简洁的对话界面
- **每个对话一个气泡** - 用户和 AI 的每条消息都独立显示
- ChatGPT 风格的设计
- 用户消息: 蓝色渐变气泡,靠右对齐
- AI 消息: 半透明白色气泡,靠左对齐
- 带头像图标 (用户/机器人)

### 3. 交互特性
- Enter 键发送消息
- Shift+Enter 换行
- 自动滚动到最新消息
- 显示消息时间戳
- 空状态提示

## 🚀 使用方法

### 访问聊天页面

1. **通过主页导航**
   - 访问 http://localhost:3000
   - 点击右上角的"聊天模式"按钮

2. **直接访问**
   - http://localhost:3000/chat

### 开始对话

1. 在输入框输入消息
2. 按 Enter 发送 (或点击发送按钮)
3. 观看 AI 实时生成回复

## 🔧 技术实现

### 后端 (FastAPI)

**文件:** `web/backend/chat_api.py`

```python
# 流式响应生成器
async def generate_stream_response(message: str):
    # 使用 Server-Sent Events 格式
    yield f"data: {json.dumps({'type': 'text', 'content': '文本'})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

# 流式 API 端点
@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    return StreamingResponse(
        generate_stream_response(request.message),
        media_type="text/event-stream"
    )
```

**集成 Claude Agent SDK:**

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
                    # 流式输出每一块文本
                    data = {"type": "text", "content": block.text}
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    # 发送完成信号
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
```

### 前端 (Next.js + React)

**文件:** `web/frontend/app/chat/page.tsx`

**核心流程:**

1. **发送消息**
   ```typescript
   const response = await fetch("http://localhost:8000/api/chat/stream", {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify({ message: userInput })
   })
   ```

2. **读取流式响应**
   ```typescript
   const reader = response.body?.getReader()
   const decoder = new TextDecoder()

   while (true) {
     const { done, value } = await reader.read()
     if (done) break

     const chunk = decoder.decode(value)
     // 解析 SSE 格式数据
     // 更新消息状态
   }
   ```

3. **实时更新 UI**
   ```typescript
   setMessages(prev => {
     const newMessages = [...prev]
     const lastMessage = newMessages[assistantMessageIndex]
     if (lastMessage && lastMessage.role === "assistant") {
       lastMessage.content += data.content  // 累加文本
     }
     return newMessages
   })
   ```

## 📝 消息格式

### 流式响应格式 (SSE)

```
data: {"type": "text", "content": "你"}

data: {"type": "text", "content": "好"}

data: {"type": "done"}
```

### Message 对象

```typescript
interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
  isStreaming?: boolean  // 流式输出中
}
```

## 🎨 UI 设计

- **渐变背景**: `from-slate-900 via-purple-900 to-slate-900`
- **用户气泡**: `from-blue-600 to-blue-700`
- **AI 气泡**: `bg-white/10 backdrop-blur-sm`
- **头像图标**:
  - 用户: `from-blue-500 to-cyan-500`
  - AI: `from-purple-500 to-pink-500`

## 🔮 待集成功能

### 1. 连接 Claude Agent SDK

当前使用模拟响应,实际部署时需要:

```python
# 1. 安装 SDK
pip install claude-agent-sdk

# 2. 替换 chat_api.py 中的 generate_stream_response 函数
# 3. 使用上面提供的 Claude Agent SDK 集成代码
```

### 2. 连接 LiteLLM

也可以使用已有的 LiteLLM 客户端:

```python
from src.llm import LiteLLMClient

async def generate_stream_response(message: str):
    llm_client = LiteLLMClient(config_path="...")

    # LiteLLM 也支持流式输出
    response = await llm_client.generate(
        prompt=message,
        model="deepseek",
        stream=True  # 启用流式
    )

    # 处理流式响应...
```

### 3. 增强功能

- 对话历史持久化
- 多轮对话上下文管理
- 不同角色/场景切换
- 导出对话记录
- 分享对话链接

## 📚 相关文档

- Claude Agent SDK: https://github.com/anthropics/claude-agent-sdk-python
- Server-Sent Events: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
- Streaming API: https://developer.mozilla.org/en-US/docs/Web/API/Streams_API
