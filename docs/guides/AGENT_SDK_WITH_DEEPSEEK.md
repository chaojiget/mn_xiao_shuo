# 使用 Claude Agent SDK + DeepSeek 模型

## 🎯 目标

使用 **Claude Agent SDK** 的强大功能（tools、MCP、多轮对话），但底层使用 **DeepSeek V3** 模型（通过 LiteLLM）。

## 🏗️ 架构

```
Claude Agent SDK
    ↓ (API 请求)
LiteLLM Proxy Server (http://localhost:4000)
    ↓ (路由)
OpenRouter → DeepSeek V3
```

### 为什么这样做？

✅ **Agent SDK 的优势**：
- 强大的工具系统 (tools)
- MCP 服务器支持
- 多轮对话管理
- Hooks 和权限控制

✅ **DeepSeek 的优势**：
- 高性价比（比 Claude 便宜很多）
- 中文理解优秀
- 性能强大

## 📦 安装依赖

```bash
# 1. 激活虚拟环境
source .venv/bin/activate

# 2. 安装 Claude Agent SDK
pip install claude-agent-sdk

# 3. 确保已安装 LiteLLM
pip install 'litellm[proxy]'
```

## 🔧 配置步骤

### 步骤 1: 配置环境变量

复制并编辑 `.env` 文件：

```bash
cp .env.example .env
nano .env
```

设置以下变量：

```bash
# OpenRouter API Key (必需)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# 启用 LiteLLM Proxy 模式
USE_LITELLM_PROXY=true
ANTHROPIC_API_BASE=http://localhost:4000
ANTHROPIC_API_KEY=sk-proxy-key  # 任意值
```

### 步骤 2: 启动 LiteLLM Proxy Server

在**新的终端窗口**中运行：

```bash
./scripts/start_litellm_proxy.sh
```

输出示例：
```
🚀 启动 LiteLLM Proxy Server (路由到 DeepSeek)
================================================
INFO: LiteLLM: Proxy running on http://0.0.0.0:4000
```

**保持这个终端窗口运行！**

### 步骤 3: 验证 Proxy 工作

在另一个终端测试：

```bash
curl http://localhost:4000/health

# 期望输出: {"status": "healthy"}
```

测试 DeepSeek 路由：

```bash
curl http://localhost:4000/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-any-key" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

### 步骤 4: 启动 Web 服务

在**另一个新终端**中：

```bash
./web/start-web.sh
```

访问: http://localhost:3001/chat

## 🧪 测试 Agent SDK

### 方式 1: 通过 Web 界面

1. 访问 http://localhost:3001/chat
2. 输入标题："星际迷航"
3. 选择类型：科幻
4. 点击"一键生成"
5. 等待生成（会使用 Agent SDK + DeepSeek）

### 方式 2: Python 脚本测试

```python
import asyncio
import os

# 设置环境变量
os.environ["USE_LITELLM_PROXY"] = "true"
os.environ["ANTHROPIC_API_BASE"] = "http://localhost:4000"
os.environ["ANTHROPIC_API_KEY"] = "sk-proxy-key"

from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

async def test_agent_with_deepseek():
    """测试 Agent SDK 通过 Proxy 使用 DeepSeek"""

    options = ClaudeAgentOptions(
        system_prompt="你是一位专业的小说设定生成助手。",
        max_turns=1
    )

    async for message in query(prompt="为科幻小说《星际迷航》生成主角设定", options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)

# 运行测试
asyncio.run(test_agent_with_deepseek())
```

保存为 `test_agent_deepseek.py`，运行：

```bash
python test_agent_deepseek.py
```

## 📊 LiteLLM Proxy 配置详解

配置文件：`config/litellm_proxy_config.yaml`

```yaml
model_list:
  # 将 claude-3-5-sonnet 请求路由到 DeepSeek
  - model_name: claude-3-5-sonnet-20241022
    litellm_params:
      model: openrouter/deepseek/deepseek-chat
      api_base: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}

  # 所有 Claude Sonnet 请求都路由到 DeepSeek
  - model_name: claude-sonnet-4-20250514
    litellm_params:
      model: openrouter/deepseek/deepseek-chat
      api_base: https://openrouter.ai/api/v1
      api_key: ${OPENROUTER_API_KEY}

router_settings:
  num_retries: 3
  request_timeout: 600

litellm_settings:
  drop_params: true  # 忽略 Claude 特有参数
```

## 🔍 工作流程说明

### 完整的请求流程

```
1. 前端发送请求
   POST /api/generate-setting
   {"title": "星际迷航", "novel_type": "scifi"}
   ↓

2. 后端检测到 USE_LITELLM_PROXY=true
   设置环境变量:
   - ANTHROPIC_API_BASE=http://localhost:4000
   - ANTHROPIC_API_KEY=sk-proxy-key
   ↓

3. Agent SDK 发送请求
   POST http://localhost:4000/v1/messages
   {
     "model": "claude-3-5-sonnet-20241022",
     "messages": [...]
   }
   ↓

4. LiteLLM Proxy 接收请求
   查找路由规则:
   claude-3-5-sonnet-20241022 → deepseek/deepseek-chat
   ↓

5. LiteLLM 转换并发送
   POST https://openrouter.ai/api/v1/chat/completions
   {
     "model": "deepseek/deepseek-chat",
     "messages": [...]
   }
   ↓

6. DeepSeek 返回响应
   ↓

7. LiteLLM Proxy 转换为 Anthropic 格式
   ↓

8. Agent SDK 接收响应
   ↓

9. 后端处理并返回前端
```

## 🛠️ 自定义工具示例

使用 Agent SDK 的工具能力：

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions, query

@tool("generate_character_name", "生成角色名称", {
    "novel_type": str,
    "role": str
})
async def generate_character_name(args):
    """生成符合小说类型的角色名称"""
    # ... 实现逻辑
    return {
        "content": [{"type": "text", "text": f"生成的名称: {name}"}]
    }

# 创建 MCP Server
server = create_sdk_mcp_server(
    name="novel-tools",
    version="1.0.0",
    tools=[generate_character_name]
)

# 配置 Agent 使用工具
options = ClaudeAgentOptions(
    mcp_servers={"novel_tools": server},
    allowed_tools=["mcp__novel_tools__generate_character_name"]
)

# 使用工具
async for msg in query("生成一个科幻主角名称", options=options):
    print(msg)
```

## 📈 性能对比

### DeepSeek V3 vs Claude Sonnet 3.5

| 指标 | DeepSeek V3 | Claude Sonnet 3.5 |
|------|-------------|-------------------|
| 价格 (输入) | $0.14/1M tokens | $3/1M tokens |
| 价格 (输出) | $0.28/1M tokens | $15/1M tokens |
| 中文理解 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 推理能力 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 速度 | 快 | 中等 |

**性价比**: DeepSeek 约为 Claude 的 **1/10 - 1/50**！

## ⚠️ 常见问题

### 问题 1: Proxy 启动失败

```bash
Error: Address already in use
```

**解决**：端口 4000 被占用，修改端口：

```bash
litellm --config config/litellm_proxy_config.yaml --port 4001
```

然后更新 `.env`：
```bash
ANTHROPIC_API_BASE=http://localhost:4001
```

### 问题 2: Agent SDK 仍在调用真实 Claude API

**检查**：
```bash
echo $ANTHROPIC_API_BASE
# 应该输出: http://localhost:4000
```

**修复**：
```bash
export USE_LITELLM_PROXY=true
export ANTHROPIC_API_BASE=http://localhost:4000
export ANTHROPIC_API_KEY=sk-proxy-key
```

### 问题 3: 生成失败或超时

**检查 Proxy 日志**：
- Proxy 终端窗口应该显示请求日志
- 检查是否有错误信息

**增加超时**：
```yaml
# config/litellm_proxy_config.yaml
router_settings:
  request_timeout: 900  # 15 分钟
```

### 问题 4: OPENROUTER_API_KEY 未设置

```bash
Error: OPENROUTER_API_KEY not found
```

**修复**：
```bash
export OPENROUTER_API_KEY=your-key-here
```

## 📚 相关文档

- [Claude Agent SDK 文档](https://github.com/anthropics/claude-agent-sdk-python)
- [LiteLLM Proxy 文档](https://docs.litellm.ai/docs/proxy/quick_start)
- [OpenRouter 文档](https://openrouter.ai/docs)
- [DeepSeek API 文档](https://platform.deepseek.com/docs)

## 🚀 下一步

现在你可以：

1. ✅ 使用 Agent SDK 的所有功能
2. ✅ 实际调用 DeepSeek 模型
3. ✅ 享受低成本 + 高性能
4. ✅ 创建自定义工具和 MCP 服务器

**开始构建你的多 Agent 跑团系统吧！** 🎉
