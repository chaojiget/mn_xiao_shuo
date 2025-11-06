# LiteLLM + Claude Agent SDK 完整指南

**终极方案**: 使用 **Claude Agent SDK** 的强大 Agent 能力,通过 **LiteLLM 代理** 调用低成本模型

---

## 🎯 架构优势

### 为什么这个方案最好?

```
┌─────────────────────────────────────────────────┐
│           你的应用 (Game/Chat/etc.)             │
└───────────────────┬─────────────────────────────┘
                    │
        ┌───────────▼──────────────┐
        │   Claude Agent SDK       │  ← Agent能力（工具、Hook等）
        │ (Anthropic官方SDK)       │
        └───────────┬──────────────┘
                    │ ANTHROPIC_BASE_URL
        ┌───────────▼──────────────┐
        │   LiteLLM Proxy          │  ← 统一网关
        │   (port 4000)            │
        └───────────┬──────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
┌───▼───┐     ┌────▼────┐     ┌───▼────┐
│DeepSeek│    │  Qwen   │    │  GPT-4 │  ← 多模型支持
│$0.001 │    │ $0.002  │    │ $0.020 │
└────────┘    └─────────┘    └────────┘
```

**优势:**
1. ✅ **Agent 能力**: 工具调用、Hook 系统、状态管理
2. ✅ **低成本**: 使用 DeepSeek/Qwen 等便宜模型
3. ✅ **灵活性**: 不同 Agent 用不同模型
4. ✅ **统一管理**: LiteLLM 代理统一管理所有模型
5. ✅ **易于切换**: 配置文件即可切换模型

---

## 📋 完整设置步骤

### Step 1: 安装依赖

```bash
# 安装 LiteLLM
pip install litellm

# 安装 Claude Agent SDK
pip install claude-agent-sdk

# 检查安装
litellm --version
python -c "import claude_agent_sdk; print('Claude Agent SDK installed')"
```

### Step 2: 配置 LiteLLM

编辑 `config/litellm_config.yaml`:

```yaml
model_list:
  # DeepSeek V3 (便宜,中文好)
  - model_name: deepseek
    litellm_params:
      model: openrouter/deepseek/deepseek-v3.1-terminus
      api_key: ${OPENROUTER_API_KEY}

  # Qwen 2.5 (中文优化)
  - model_name: qwen
    litellm_params:
      model: openrouter/qwen/qwen-2.5-72b-instruct
      api_key: ${OPENROUTER_API_KEY}

  # Claude Sonnet (高质量)
  - model_name: claude-sonnet
    litellm_params:
      model: openrouter/anthropic/claude-3.5-sonnet
      api_key: ${OPENROUTER_API_KEY}

  # GPT-4 (备用)
  - model_name: gpt-4
    litellm_params:
      model: openrouter/openai/gpt-4
      api_key: ${OPENROUTER_API_KEY}

router_settings:
  num_retries: 2
  timeout: 60
  default_max_parallel_requests: 100
```

### Step 3: 启动 LiteLLM 代理

```bash
# 设置环境变量
export OPENROUTER_API_KEY="sk-or-v1-..."
export LITELLM_MASTER_KEY="sk-litellm-$(openssl rand -hex 16)"

# 启动 LiteLLM 代理服务器
litellm --config ./config/litellm_config.yaml --port 4000

# 输出:
# INFO: LiteLLM Proxy running on http://0.0.0.0:4000
```

**保持这个终端运行!**

### Step 4: 配置 Claude Agent SDK

新开一个终端,设置环境变量:

```bash
# 让 Claude Agent SDK 使用 LiteLLM 代理
export ANTHROPIC_BASE_URL="http://0.0.0.0:4000"
export ANTHROPIC_AUTH_TOKEN="$LITELLM_MASTER_KEY"

# 或者设置到 .env 文件
cat >> .env << EOF
LITELLM_MASTER_KEY=sk-litellm-your-key-here
ANTHROPIC_BASE_URL=http://0.0.0.0:4000
ANTHROPIC_AUTH_TOKEN=\${LITELLM_MASTER_KEY}
EOF
```

### Step 5: 测试连接

```python
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions

async def test():
    # 测试通过 LiteLLM 代理调用 DeepSeek
    opts = ClaudeAgentOptions(max_turns=1)
    async for msg in query(prompt="你好，请告诉我你是哪个模型?", options=opts):
        print(msg)

anyio.run(test)
```

**预期输出:**
```
AssistantMessage(content=[TextBlock(text="你好！我是DeepSeek V3...")])
```

---

## 🔧 使用方法

### 方法 1: 直接使用 (简单任务)

```python
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions

async def simple_query():
    # 默认使用配置的第一个模型 (deepseek)
    async for msg in query(prompt="讲个笑话"):
        print(msg)

anyio.run(simple_query)
```

### 方法 2: 使用我们的 Agent 配置系统 (推荐)

#### 2.1 配置 Agent (config/llm_agents.yaml)

```yaml
agents:
  game_master:
    backend: "claude"
    use_litellm_proxy: true
    model: "deepseek"  # 通过代理调用 DeepSeek
    temperature: 0.8
    max_tokens: 2000
    allowed_tools: ["Read", "Write", "Bash"]

  npc_dialogue:
    backend: "claude"
    use_litellm_proxy: true
    model: "qwen"  # 通过代理调用 Qwen
    temperature: 0.9
    max_tokens: 1000
```

#### 2.2 在代码中使用

```python
from llm.agent_config import load_agent_backend

# 加载游戏主持人 Agent (使用 DeepSeek)
game_master = load_agent_backend("game_master")

# 加载 NPC 对话 Agent (使用 Qwen)
npc_agent = load_agent_backend("npc_dialogue")

# 生成响应
response = await game_master.generate(messages=[
    LLMMessage(role="user", content="开始游戏")
])
print(response.content)
```

### 方法 3: 动态切换模型

```python
from llm import create_backend

# 创建不同模型的后端
deepseek_agent = create_backend("claude", {
    "use_litellm_proxy": True,
    "model": "deepseek",
    "temperature": 0.7
})

qwen_agent = create_backend("claude", {
    "use_litellm_proxy": True,
    "model": "qwen",
    "temperature": 0.8
})

gpt4_agent = create_backend("claude", {
    "use_litellm_proxy": True,
    "model": "gpt-4",
    "temperature": 0.6
})
```

---

## 📊 成本对比

### 场景: 每天运行 100 次 Agent 调用

| Agent | 模型 | 成本/调用 | 日成本 | 月成本 | 年成本 |
|-------|------|----------|--------|--------|--------|
| Game Master | DeepSeek | $0.001 | $0.10 | $3.00 | $36 |
| NPC Dialogue | Qwen | $0.002 | $0.20 | $6.00 | $72 |
| Combat System | DeepSeek | $0.001 | $0.05 | $1.50 | $18 |
| Quest Manager | DeepSeek | $0.001 | $0.03 | $0.90 | $11 |
| World Generator | Claude | $0.015 | $0.15 | $4.50 | $54 |
| **总计** | **混合** | **-** | **$0.53** | **$16** | **$191** |

**对比全部使用 Claude Sonnet:**
- 成本: 100 × $0.015 = $1.50/天 = $45/月 = **$540/年**
- **节省: 65%**

**对比全部使用 DeepSeek (无 Agent 能力):**
- 成本: 100 × $0.001 = $0.10/天 = $3/月 = $36/年
- 但没有 Agent 的工具调用、Hook 等高级功能

**我们的方案:**
- ✅ Agent 能力: 完整
- ✅ 成本: 仅比纯 DeepSeek 高 $13/月
- ✅ 灵活性: 关键任务可用高质量模型

---

## 🎮 实战案例

### 案例 1: 游戏主持人 (Game Master)

```python
from llm.agent_config import load_agent_backend
from llm.base import LLMMessage

# 加载配置好的 Game Master Agent
gm = load_agent_backend("game_master")

# Agent 配置:
# - Model: DeepSeek (成本低,中文好)
# - Temperature: 0.8 (有创意)
# - Tools: Read, Write, Bash

# 生成游戏场景
messages = [
    LLMMessage(role="system", content="你是游戏主持人"),
    LLMMessage(role="user", content="玩家进入了迷雾森林")
]

response = await gm.generate(messages)
print(response.content)
```

### 案例 2: 多 NPC 对话 (不同个性)

```python
# 老者 NPC (使用 Qwen,温度0.6)
elder_npc = create_backend("claude", {
    "use_litellm_proxy": True,
    "model": "qwen",
    "temperature": 0.6,  # 稳重
    "system_prompt": "你是一位睿智的老者"
})

# 商人 NPC (使用 DeepSeek,温度0.9)
merchant_npc = create_backend("claude", {
    "use_litellm_proxy": True,
    "model": "deepseek",
    "temperature": 0.9,  # 活泼
    "system_prompt": "你是一位精明的商人"
})

# 生成对话
elder_response = await elder_npc.generate([
    LLMMessage(role="user", content="请教您关于古老传说")
])

merchant_response = await merchant_npc.generate([
    LLMMessage(role="user", content="有什么好货推荐?")
])
```

### 案例 3: 任务复杂度路由

```python
async def smart_route(task):
    """根据任务复杂度选择模型"""

    if task.complexity < 3:
        # 简单任务 → DeepSeek (便宜)
        agent = create_backend("claude", {
            "use_litellm_proxy": True,
            "model": "deepseek"
        })
    elif task.complexity < 7:
        # 中等任务 → Qwen (平衡)
        agent = create_backend("claude", {
            "use_litellm_proxy": True,
            "model": "qwen"
        })
    else:
        # 复杂任务 → Claude Sonnet (高质量)
        agent = create_backend("claude", {
            "use_litellm_proxy": True,
            "model": "claude-sonnet"
        })

    return await agent.generate(task.messages)
```

---

## 🚀 高级功能

### 1. 工具调用 (Tool Use)

```python
from claude_agent_sdk import ClaudeAgentOptions

# 配置允许的工具
opts = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Bash"],
    max_turns=5  # 允许多轮对话
)

async for msg in query(
    prompt="创建一个 hello.py 文件",
    options=opts
):
    print(msg)
```

**Agent 会自动:**
1. 分析任务
2. 调用 `Write` 工具
3. 创建文件
4. 返回结果

### 2. Hook 系统

```python
from claude_agent_sdk import HookMatcher

async def check_bash_command(input_data, tool_use_id, context):
    """阻止危险的 Bash 命令"""
    if input_data["tool_name"] == "Bash":
        command = input_data["tool_input"].get("command", "")

        # 阻止 rm -rf
        if "rm -rf" in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "危险命令被阻止"
                }
            }
    return {}

opts = ClaudeAgentOptions(
    allowed_tools=["Bash"],
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash", hooks=[check_bash_command])
        ]
    }
)
```

### 3. 自定义 MCP Server

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("roll_dice", "投骰子", {"sides": int})
async def roll_dice(args):
    import random
    result = random.randint(1, args["sides"])
    return {
        "content": [
            {"type": "text", "text": f"投掷了{args['sides']}面骰子,结果是{result}"}
        ]
    }

# 创建 MCP Server
dice_server = create_sdk_mcp_server(
    name="game-tools",
    version="1.0.0",
    tools=[roll_dice]
)

# 使用
opts = ClaudeAgentOptions(
    mcp_servers={"game": dice_server},
    allowed_tools=["mcp__game__roll_dice"]
)

async for msg in query("帮我投一个20面骰子", options=opts):
    print(msg)
```

---

## ⚙️ 配置文件完整示例

### config/llm_agents.yaml

```yaml
global:
  litellm_proxy_url: "http://0.0.0.0:4000"
  litellm_master_key: ${LITELLM_MASTER_KEY}
  default_temperature: 0.7
  default_max_tokens: 4096

agents:
  # 主要游戏引擎
  game_master:
    backend: "claude"
    use_litellm_proxy: true
    model: "deepseek"
    temperature: 0.8
    max_tokens: 2000
    allowed_tools: ["Read", "Write", "Bash"]
    system_prompt: "你是专业的游戏主持人(Game Master)"

  # NPC 对话系统
  npc_dialogue:
    backend: "claude"
    use_litellm_proxy: true
    model: "qwen"
    temperature: 0.9
    max_tokens: 1000
    allowed_tools: []
    system_prompt: "你扮演游戏中的 NPC，要有个性和情感"

  # 战斗系统
  combat_system:
    backend: "claude"
    use_litellm_proxy: true
    model: "deepseek"
    temperature: 0.5
    max_tokens: 1500
    allowed_tools: ["Bash"]
    system_prompt: "你是战斗系统，负责计算伤害和判定"

  # 世界生成器 (使用高质量模型)
  world_generator:
    backend: "claude"
    use_litellm_proxy: true
    model: "claude-sonnet"
    temperature: 0.8
    max_tokens: 3000
    allowed_tools: ["Write"]
    system_prompt: "你是世界生成器，创造丰富的世界观"
```

---

## 🐛 故障排除

### 问题 1: LiteLLM 代理启动失败

```bash
# 检查端口是否被占用
lsof -i :4000

# 杀死占用进程
kill -9 <PID>

# 重新启动
litellm --config ./config/litellm_config.yaml --port 4000
```

### 问题 2: Claude Agent SDK 无法连接代理

```bash
# 检查环境变量
echo $ANTHROPIC_BASE_URL  # 应该是 http://0.0.0.0:4000
echo $ANTHROPIC_AUTH_TOKEN  # 应该是 sk-litellm-...

# 测试代理
curl http://0.0.0.0:4000/health
# 应该返回: {"status": "healthy"}

# 测试模型调用
curl -X POST http://0.0.0.0:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### 问题 3: 模型调用失败

**检查 LiteLLM 配置:**

```bash
# 查看 LiteLLM 日志
# 终端应该显示每个请求的日志

# 常见错误:
# - API Key 未设置: 检查 OPENROUTER_API_KEY
# - 模型名称错误: 检查 litellm_config.yaml 中的 model_name
# - 网络问题: 检查网络连接
```

---

## 📚 相关文档

- [LiteLLM 官方文档](https://docs.litellm.ai)
- [Claude Agent SDK GitHub](https://github.com/anthropics/claude-agent-sdk-python)
- [OpenRouter API 文档](https://openrouter.ai/docs)
- [本项目 LLM 后端指南](./LLM_BACKEND_GUIDE.md)
- [Agent 配置示例](../config/llm_agents.yaml)

---

## 🎓 最佳实践

### 1. 根据任务选择模型

```python
# 叙事生成 → DeepSeek (中文好,便宜)
# NPC 对话 → Qwen (对话优化)
# 代码生成 → GPT-4 (代码能力强)
# 创意写作 → Claude Sonnet (高质量)
```

### 2. 合理设置温度

```python
# 逻辑计算 → 0.3-0.5 (准确)
# 正常对话 → 0.6-0.8 (平衡)
# 创意内容 → 0.8-1.0 (有创意)
```

### 3. 使用工具时设置权限

```python
opts = ClaudeAgentOptions(
    allowed_tools=["Read"],  # 只读,安全
    # 避免: ["Bash"]  # 危险!
)
```

### 4. 监控成本

```python
# 记录每次调用
async def log_cost(model, tokens):
    cost_per_1k = {
        "deepseek": 0.0007,
        "qwen": 0.0014,
        "claude-sonnet": 0.011
    }
    cost = (tokens / 1000) * cost_per_1k[model]
    print(f"[COST] {model}: ${cost:.4f}")
```

---

## 🏆 总结

### 最佳配置方案

```yaml
# 90% 的任务使用 DeepSeek (便宜)
# 5% 的对话使用 Qwen (中文好)
# 5% 的关键任务使用 Claude (质量高)
```

**成本估算:**
- 月成本: ~$16
- 对比纯 Claude: 节省 65%
- Agent 能力: 完整

**适用场景:**
- ✅ 文字冒险游戏
- ✅ 聊天机器人
- ✅ 内容生成
- ✅ 代码助手
- ✅ 任何需要 Agent 能力但成本敏感的项目

---

**最后更新**: 2025-11-01
**版本**: v1.0
**作者**: AI Assistant
