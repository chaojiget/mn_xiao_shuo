# 流式输出实现说明

## 概述

已将 Web 聊天界面的模拟流式输出替换为真实的 AI 流式响应。现在使用 **LiteLLM + DeepSeek V3** 模型实时生成小说内容。

## 实现细节

### 后端实现 (web/backend/chat_api.py)

**核心改动:**
- 替换 `generate_stream_response()` 函数,使用真实的 LiteLLM 流式 API
- 使用 `llm_client.router.acompletion(stream=True)` 启用流式输出
- 逐块接收 AI 生成的内容,通过 Server-Sent Events (SSE) 推送到前端
- **新增**: 小说设定作为系统提示词注入
- **新增**: 对话历史管理（最近 10 条消息）
- **新增**: 上下文连贯性保持

**技术栈:**
- **LiteLLM Router**: 统一的 LLM 客户端
- **OpenRouter**: LLM API 网关
- **DeepSeek V3**: 主力生成模型 (性价比高,中文友好)
- **FastAPI StreamingResponse**: 流式响应容器
- **Server-Sent Events**: 实时数据推送协议
- **Pydantic Models**: 数据验证（NovelSettings, ChatRequest）

**流式输出流程:**
```
用户输入 → FastAPI 端点 → generate_stream_response()
    ↓
LiteLLM Router (stream=True)
    ↓
OpenRouter API → DeepSeek V3
    ↓
逐块返回 delta.content
    ↓
封装为 SSE 格式: data: {"type": "text", "content": "..."}
    ↓
前端实时接收并显示
    ↓
完成后发送: data: {"type": "done"}
```

### 前端实现 (web/frontend/app/chat/page.tsx)

**已有功能 (无需修改):**
- 使用 `fetch()` 调用 `/api/chat/stream` 端点
- 通过 `response.body.getReader()` 读取流式数据
- 解析 SSE 格式 `data: {...}`
- 实时更新最后一条消息的 `content`
- 显示流式光标动画 (`isStreaming` 状态)

## 配置要求

### 环境变量 (.env)

确保设置了以下环境变量:
```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### LiteLLM 配置 (config/litellm_config.yaml)

当前配置使用 DeepSeek V3:
```yaml
model_list:
  - model_name: deepseek
    litellm_params:
      model: openrouter/deepseek/deepseek-v3.1-terminus
      api_base: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}
```

## 使用方法

### 启动服务

```bash
# 一键启动 (后端 + 前端)
./web/start-web.sh

# 或手动启动后端
cd web/backend
source ../../.venv/bin/activate
uvicorn main:app --reload --port 8000

# 或手动启动前端
cd web/frontend
npm run dev
```

### 访问界面

1. 打开浏览器访问: http://localhost:3000/chat
2. 填写小说设定或选择已有小说
3. 点击"开始创作"
4. 输入创作需求,实时查看 AI 生成的内容

### 快捷操作

界面提供 4 个快捷按钮:
- **生成下一章**: 自动生成下一章节内容
- **角色对话**: 生成精彩的角色对话场景
- **场景描写**: 详细描写当前场景
- **埋下伏笔**: 为后续剧情埋下线索

## 代码位置

### 关键文件

| 文件 | 说明 | 关键函数/组件 |
|------|------|---------------|
| `web/backend/chat_api.py` | 聊天 API 路由 | `generate_stream_response()` |
| `web/frontend/app/chat/page.tsx` | 聊天界面组件 | `generateContent()`, `ChatPage` |
| `web/backend/main.py` | FastAPI 主入口 | 注册 `chat_router` |
| `src/llm/litellm_client.py` | LLM 客户端 | `LiteLLMClient` |
| `config/litellm_config.yaml` | 模型配置 | 模型列表与路由设置 |

### 核心代码片段

**后端流式生成 (chat_api.py:29-75):**
```python
async def generate_stream_response(message: str) -> AsyncGenerator[str, None]:
    global llm_client

    if llm_client is None:
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config" / "litellm_config.yaml"
        llm_client = LiteLLMClient(config_path=str(config_path))

    try:
        messages = [{"role": "user", "content": message}]

        response = await llm_client.router.acompletion(
            model="deepseek",
            messages=messages,
            temperature=0.8,
            max_tokens=4000,
            stream=True
        )

        async for chunk in response:
            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    data = {"type": "text", "content": delta.content}
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    except Exception as e:
        error_data = {"type": "text", "content": f"\n\n[错误: {str(e)}]"}
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
```

**前端流式接收 (page.tsx:205-247):**
```typescript
const reader = response.body?.getReader()
const decoder = new TextDecoder()

if (reader) {
  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value)
    const lines = chunk.split("\n\n")

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = JSON.parse(line.slice(6))

        if (data.type === "text") {
          assistantContent += data.content
          setMessages(prev => {
            const newMessages = [...prev]
            const lastMessage = newMessages[newMessages.length - 1]
            if (lastMessage && lastMessage.role === "assistant") {
              lastMessage.content = assistantContent
            }
            return newMessages
          })
        } else if (data.type === "done") {
          setMessages(prev => {
            const newMessages = [...prev]
            const lastMessage = newMessages[newMessages.length - 1]
            if (lastMessage) {
              lastMessage.isStreaming = false
            }
            return newMessages
          })
        }
      }
    }
  }
}
```

## 测试建议

### 基础功能测试

1. **启动服务测试**:
   ```bash
   cd web/backend
   source ../../.venv/bin/activate
   uvicorn main:app --reload --port 8000
   ```
   确认终端输出:
   ```
   ✅ LLM 客户端已初始化
   ✅ 数据库已连接
   ```

2. **API 端点测试**:
   ```bash
   curl -X POST http://localhost:8000/api/chat/stream \
     -H "Content-Type: application/json" \
     -d '{"message": "测试流式输出"}' \
     --no-buffer
   ```

   期望输出:
   ```
   data: {"type": "text", "content": "这"}
   data: {"type": "text", "content": "是"}
   data: {"type": "text", "content": "一"}
   ...
   data: {"type": "done"}
   ```

3. **前端界面测试**:
   - 访问 http://localhost:3000/chat
   - 填写小说设定
   - 输入: "生成一个科幻小说的开头"
   - 观察是否有实时流式输出

### 性能测试

- **响应时间**: 首字延迟应 < 2 秒
- **流式速度**: 应感受到逐字/逐块输出效果
- **并发测试**: 同时开启 2-3 个聊天窗口

### 错误处理测试

1. **无效 API Key**: 移除 `.env` 中的 `OPENROUTER_API_KEY`
   - 期望: 错误信息显示在聊天界面

2. **网络超时**: 断开网络后发送消息
   - 期望: 显示错误提示

3. **模型不存在**: 修改 `chat_api.py` 中的 `model="invalid_model"`
   - 期望: 错误信息正确返回前端

## 常见问题

### 问题 1: 流式输出卡顿或延迟高

**可能原因:**
- OpenRouter API 响应慢
- 网络延迟
- DeepSeek 模型负载高

**解决方案:**
- 检查网络连接
- 降低 `max_tokens` 参数 (当前 4000)
- 尝试更换模型 (如 `claude-haiku`)

### 问题 2: 无法连接到 LiteLLM

**检查项:**
1. 确认 `config/litellm_config.yaml` 存在
2. 确认 `.env` 中有 `OPENROUTER_API_KEY`
3. 检查终端输出是否有初始化错误

### 问题 3: 前端收不到流式数据

**排查步骤:**
1. 打开浏览器开发者工具 → Network 标签
2. 查看 `/api/chat/stream` 请求状态
3. 确认 Response Headers 包含 `text/event-stream`
4. 确认 Response 有持续的数据流

**调试代码:**
```typescript
// 在 page.tsx 中添加日志
const chunk = decoder.decode(value)
console.log("收到数据块:", chunk)  // 添加此行
```

## 后续优化方向

### 1. 对话历史管理
当前每次请求都是独立的,可以添加对话历史:
```python
# chat_api.py
class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None
    history: List[Dict[str, str]] = []  # 添加历史消息

# 在 generate_stream_response 中:
messages = request.history + [{"role": "user", "content": request.message}]
```

### 2. 小说设定上下文注入
将小说设定作为系统提示词:
```python
system_prompt = f"""你是一位专业的小说创作助手。

小说信息:
- 标题: {novel_settings.title}
- 类型: {novel_settings.type}
- 主角: {novel_settings.protagonist}
- 背景: {novel_settings.background}

请根据以上设定生成内容。"""

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": message}
]
```

### 3. 分角色对话支持
为不同角色使用不同的系统提示词:
```python
if character == "主角":
    system_prompt = f"你现在扮演主角 {protagonist_name}，性格: {personality}"
elif character == "旁白":
    system_prompt = "你是全知全能的旁白,客观描述场景和剧情"
```

### 4. 流式输出优化
- 添加 token 使用量统计
- 实现打字机效果速度控制
- 添加"暂停/继续"功能

### 5. 错误重试机制
```python
async def generate_stream_response_with_retry(message: str, max_retries=3):
    for attempt in range(max_retries):
        try:
            async for chunk in generate_stream_response(message):
                yield chunk
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # 指数退避
```

## 相关文档

- [LiteLLM 文档](https://docs.litellm.ai/)
- [OpenRouter API 文档](https://openrouter.ai/docs)
- [FastAPI 流式响应](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [Server-Sent Events 规范](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [DeepSeek 模型文档](https://platform.deepseek.com/docs)

## 变更日志

**2025-10-30 (第二次更新)**
- ✅ 添加小说设定上下文注入（系统提示词）
- ✅ 实现对话历史管理（保留最近 10 条）
- ✅ 优化前端历史记录传递逻辑
- ✅ 创建测试脚本 `test_chat_stream.py`
- ✅ 更新 API 文档注释

**2025-10-30 (初始版本)**
- ✅ 替换模拟流式输出为真实 LiteLLM 流式 API
- ✅ 使用 DeepSeek V3 模型
- ✅ 实现完整的错误处理
- ✅ 编写测试指南和文档
