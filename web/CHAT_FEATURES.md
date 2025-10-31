# 聊天功能特性说明

## 最新更新 (2025-10-30)

已完成聊天界面的以下增强功能：

### ✅ 真实 AI 流式输出

**替换模拟数据**：将前端的模拟流式输出替换为真实的 LiteLLM + DeepSeek V3 流式响应

**技术实现**：
- 后端：`web/backend/chat_api.py` 使用 `llm_client.router.acompletion(stream=True)`
- 前端：保持原有的 SSE 读取逻辑不变
- 格式：`data: {"type": "text", "content": "..."}`

### ✅ 小说设定上下文注入

**系统提示词**：将小说设定自动转换为系统提示词，指导 AI 生成符合设定的内容

**示例提示词**：
```
你是一位专业的小说创作助手。

当前创作的小说信息:
- 标题: 《星际迷航》
- 类型: 科幻
- 主角设定: 年轻的星际飞行员，勇敢且充满好奇心
- 世界背景: 2350年，人类已经掌握了星际旅行技术

请根据以上设定生成内容，注意：
1. 保持世界观和人物设定的一致性
2. 使用生动的描写和对话
3. 注意情节的连贯性和张力
4. 可以适当埋下伏笔和线索
5. 输出格式为流畅的中文小说文本
```

**效果**：AI 会根据这些设定生成内容，避免出现与世界观矛盾的元素

### ✅ 对话历史管理

**历史记录传递**：前端自动收集并发送最近 10 条对话历史

**前端实现** (page.tsx:174-181)：
```typescript
const history = messages
  .filter(msg => msg.role !== "system")
  .slice(-10)
  .map(msg => ({
    role: msg.role,
    content: msg.content
  }))
```

**后端实现** (chat_api.py:90-92)：
```python
# 添加历史消息（保留最近 10 条）
if history:
    messages.extend(history[-10:])
```

**效果**：AI 能记住之前的对话内容，生成连贯的剧情

### ✅ CORS 配置优化

**修复**：调整了 CORS 中间件的注册顺序，确保在路由注册之前添加

**修改** (main.py:21-31)：
```python
# CORS 配置（必须在路由注册之前）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册聊天路由
app.include_router(chat_router)
```

## 数据模型

### NovelSettings (chat_api.py:23-30)

```python
class NovelSettings(BaseModel):
    """小说设定"""
    id: str = None
    title: str = ""
    type: str = "scifi"  # scifi | xianxia
    protagonist: str = ""
    background: str = ""
    characters: list = []
```

### ChatRequest (chat_api.py:33-38)

```python
class ChatRequest(BaseModel):
    """聊天请求"""
    message: str                        # 用户消息
    conversation_id: str = None         # 会话 ID（可选）
    novel_settings: NovelSettings = None # 小说设定
    history: list = []                  # 对话历史
```

## API 接口

### POST /api/chat/stream

**流式聊天接口**

**请求体**：
```json
{
  "message": "生成一个科幻小说的开头",
  "novel_settings": {
    "title": "星际迷航",
    "type": "scifi",
    "protagonist": "年轻的星际飞行员",
    "background": "2350年，人类已掌握星际旅行"
  },
  "history": [
    {"role": "user", "content": "之前的问题"},
    {"role": "assistant", "content": "之前的回答"}
  ]
}
```

**响应格式** (SSE)：
```
data: {"type": "text", "content": "这"}
data: {"type": "text", "content": "是"}
data: {"type": "text", "content": "生成"}
data: {"type": "text", "content": "的"}
data: {"type": "text", "content": "内容"}
...
data: {"type": "done"}
```

## 使用流程

### 1. 启动服务

```bash
# 后端
cd web/backend
source ../../.venv/bin/activate
uvicorn main:app --reload --port 8000

# 前端（新终端）
cd web/frontend
npm run dev
```

### 2. 访问界面

打开浏览器访问: http://localhost:3000/chat

### 3. 操作步骤

1. **选择已有小说** 或 **创建新小说**
   - 左侧面板会显示已有小说列表
   - 点击小说自动加载设定

2. **填写小说设定**（如果创建新小说）
   - 小说标题
   - 类型（科幻/玄幻）
   - 主角设定
   - 世界背景

3. **点击"开始创作"**
   - 进入聊天界面
   - 系统会根据设定生成欢迎消息

4. **使用快捷按钮或输入需求**
   - 快捷按钮：生成下一章、角色对话、场景描写、埋下伏笔
   - 自由输入：如"描写主角第一次进入星舰的场景"

5. **实时查看生成结果**
   - 内容会逐字逐句流式显示
   - 可以中途停止（关闭页面）
   - 历史对话自动保存在本地状态

## 测试方法

### 方法 1: Web 界面测试

1. 访问 http://localhost:3000/chat
2. 填写设定或选择已有小说
3. 输入："生成一个科幻小说的开头"
4. 观察是否有实时流式输出

### 方法 2: Python 脚本测试

```bash
# 使用测试脚本
python test_chat_stream.py
```

脚本会执行两个测试：
1. 基础流式输出测试
2. 带历史记录的多轮对话测试

### 方法 3: curl 测试

```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "测试流式输出",
    "novel_settings": {
      "title": "测试小说",
      "type": "scifi",
      "protagonist": "测试主角",
      "background": "测试背景"
    },
    "history": []
  }' \
  --no-buffer
```

期望看到：
```
data: {"type": "text", "content": "测"}
data: {"type": "text", "content": "试"}
...
data: {"type": "done"}
```

## 技术细节

### 消息构建流程 (chat_api.py:84-95)

```python
# 1. 构建系统提示词（包含小说设定）
messages = [{"role": "system", "content": system_prompt}]

# 2. 添加历史消息（最近 10 条）
if history:
    messages.extend(history[-10:])

# 3. 添加当前用户消息
messages.append({"role": "user", "content": message})

# 4. 发送给 LiteLLM
response = await llm_client.router.acompletion(
    model="deepseek",
    messages=messages,
    temperature=0.8,
    max_tokens=4000,
    stream=True
)
```

### 流式响应处理 (chat_api.py:107-115)

```python
async for chunk in response:
    if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
        delta = chunk.choices[0].delta
        if hasattr(delta, 'content') and delta.content:
            data = {
                "type": "text",
                "content": delta.content
            }
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
```

### 前端历史记录管理 (page.tsx:174-192)

```typescript
const generateContent = async (userInput: string) => {
  // 构建对话历史（只发送最近 10 条消息，排除系统消息）
  const history = messages
    .filter(msg => msg.role !== "system")
    .slice(-10)
    .map(msg => ({
      role: msg.role,
      content: msg.content
    }))

  const response = await fetch("http://localhost:8000/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: userInput,
      novel_settings: settings,
      history: history
    })
  })
  // ... SSE 读取逻辑
}
```

## 性能参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 模型 | deepseek | DeepSeek V3 (中文友好) |
| 温度 | 0.8 | 平衡创造性和连贯性 |
| 最大 Token | 4000 | 适合章节级别的内容 |
| 历史条数 | 10 | 保持上下文不超限 |
| 首字延迟 | < 2 秒 | 典型响应时间 |

## 已知限制

1. **历史记录仅在前端保存**
   - 刷新页面会丢失历史
   - 计划：添加数据库持久化

2. **无法暂停/恢复流式输出**
   - 只能等待完成或关闭页面
   - 计划：添加 AbortController 支持

3. **无 token 使用量统计**
   - 无法了解生成成本
   - 计划：添加 usage 统计

4. **单一模型**
   - 当前只使用 DeepSeek V3
   - 计划：支持模型切换

## 后续优化方向

### 优先级 1: 数据持久化

- 将对话历史保存到数据库
- 支持会话恢复
- 导出对话记录

### 优先级 2: 用户体验

- 添加"暂停/继续"按钮
- 添加"重新生成"功能
- 显示生成进度（字数、耗时）

### 优先级 3: 高级功能

- 分角色对话支持（多个 AI 角色）
- 自定义系统提示词
- 模型切换（Claude、GPT-4 等）

### 优先级 4: 性能优化

- 实现错误重试机制
- 添加请求队列
- 优化流式速度控制

## 相关文件

| 文件 | 说明 |
|------|------|
| `web/backend/chat_api.py` | 聊天 API 路由和流式生成逻辑 |
| `web/frontend/app/chat/page.tsx` | 聊天界面组件 |
| `web/backend/main.py` | FastAPI 主入口 |
| `test_chat_stream.py` | 测试脚本 |
| `web/STREAMING_IMPLEMENTATION.md` | 流式输出技术文档 |
| `web/CHAT_FEATURES.md` | 本文档 |

## 常见问题

### Q: 流式输出卡顿怎么办？

A: 检查以下几点：
1. 网络连接是否稳定
2. OpenRouter API 是否正常
3. DeepSeek 模型是否负载过高
4. 尝试降低 max_tokens 参数

### Q: AI 生成的内容不符合设定？

A: 检查以下几点：
1. 小说设定是否填写完整
2. 主角设定和背景是否清晰
3. 尝试更明确的用户指令
4. 可以在消息中重申设定

### Q: 对话历史不连贯？

A: 检查以下几点：
1. 是否刷新了页面（会丢失历史）
2. 历史消息是否正确传递（查看网络请求）
3. 后端是否正确添加历史到 messages

### Q: CORS 错误？

A: 检查以下几点：
1. 前端访问地址是否为 localhost:3000
2. 后端 CORS 配置是否包含该地址
3. CORS 中间件是否在路由注册之前

## 更新日志

**2025-10-30 v2**
- ✅ 添加小说设定上下文注入
- ✅ 实现对话历史管理
- ✅ 修复 CORS 配置问题
- ✅ 创建测试脚本
- ✅ 编写完整功能文档

**2025-10-30 v1**
- ✅ 替换模拟流式输出为真实 AI 流式
- ✅ 集成 LiteLLM + DeepSeek V3
- ✅ 实现 SSE 流式响应
- ✅ 基础错误处理
