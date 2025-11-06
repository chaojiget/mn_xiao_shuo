# LLM Backend 使用指南

本指南介绍如何在文字冒险游戏项目中使用 LLM 后端系统。

---

## 📚 目录

1. [快速开始](#快速开始)
2. [架构概览](#架构概览)
3. [使用方法](#使用方法)
4. [游戏工具](#游戏工具)
5. [配置说明](#配置说明)
6. [最佳实践](#最佳实践)

---

## 快速开始

### 方法 1: 使用配置加载器 (推荐)

```python
from llm.agent_config import load_agent_backend
from llm.base import LLMMessage

# 加载预配置的 Agent
game_master = load_agent_backend("game_master")

# 生成响应
messages = [
    LLMMessage(role="system", content="你是游戏主持人"),
    LLMMessage(role="user", content="开始游戏")
]

response = await game_master.generate(messages)
print(response.content)
```

### 方法 2: 直接创建后端

```python
from llm import create_backend
from llm.base import LLMMessage

# 创建 LiteLLM 后端 (成本低)
litellm_backend = create_backend("litellm", {
    "model": "deepseek",
    "temperature": 0.7
})

# 创建 Claude 后端 (功能强)
claude_backend = create_backend("claude", {
    "use_litellm_proxy": True,  # 通过 LiteLLM 代理
    "model": "deepseek",
    "temperature": 0.8,
    "allowed_tools": ["Read", "Write"]
})

# 使用
messages = [LLMMessage(role="user", content="你好")]
response = await claude_backend.generate(messages)
```

---

## 架构概览

### 三种使用模式

```
模式 1: LiteLLM 直接调用
┌──────────┐     ┌──────────┐     ┌──────────┐
│   应用   │ --> │ LiteLLM  │ --> │ DeepSeek │
└──────────┘     └──────────┘     └──────────┘
成本: 低 | 功能: 基础 | 适用: 简单对话

模式 2: Claude Agent SDK 直接调用
┌──────────┐     ┌──────────┐     ┌──────────┐
│   应用   │ --> │ Claude   │ --> │  Claude  │
│          │     │Agent SDK │     │   API    │
└──────────┘     └──────────┘     └──────────┘
成本: 高 | 功能: 完整 | 适用: 高质量任务

模式 3: Claude Agent SDK + LiteLLM 代理 (推荐!)
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   应用   │ --> │ Claude   │ --> │ LiteLLM  │ --> │ DeepSeek │
│          │     │Agent SDK │     │  Proxy   │     │ /Qwen/... │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
成本: 低 | 功能: 完整 | 适用: 所有场景
```

### 统一接口

所有后端都实现了 `LLMBackend` 接口:

```python
class LLMBackend(ABC):
    async def generate(messages, tools=None, **kwargs) -> LLMResponse
    async def generate_structured(messages, response_schema, **kwargs) -> Dict
    async def generate_stream(messages, **kwargs) -> AsyncIterator[str]
```

---

## 使用方法

### 1. 基础文本生成

```python
from llm.agent_config import load_agent_backend
from llm.base import LLMMessage

# 加载 Agent
gm = load_agent_backend("game_master")

# 生成文本
messages = [
    LLMMessage(role="system", content="你是游戏主持人"),
    LLMMessage(role="user", content="描述一个神秘的森林")
]

response = await gm.generate(messages)
print(response.content)  # 生成的文本
print(response.model)    # 使用的模型
print(response.metadata) # 额外信息 (tokens, latency等)
```

### 2. 结构化输出

```python
# 定义响应 Schema
schema = {
    "type": "object",
    "properties": {
        "location": {"type": "string"},
        "description": {"type": "string"},
        "mood": {"type": "string", "enum": ["mysterious", "dangerous", "peaceful"]}
    },
    "required": ["location", "description", "mood"]
}

# 生成结构化响应
result = await gm.generate_structured(
    messages=[LLMMessage(role="user", content="创建一个新地点")],
    response_schema=schema
)

print(result["location"])     # "迷雾森林"
print(result["description"])  # "笼罩在永恒迷雾中的古老森林..."
print(result["mood"])         # "mysterious"
```

### 3. 流式输出

```python
# 流式生成 (用于实时显示)
async for chunk in gm.generate_stream(messages):
    print(chunk, end="", flush=True)
```

### 4. 工具调用 (仅 Claude Backend)

```python
from llm import create_backend
from llm.base import LLMTool, LLMMessage

# 定义工具
tools = [
    LLMTool(
        name="check_inventory",
        description="查看玩家背包",
        input_schema={
            "type": "object",
            "properties": {}
        }
    )
]

# 创建支持工具的 Claude Backend
claude = create_backend("claude", {
    "use_litellm_proxy": True,
    "model": "deepseek",
    "allowed_tools": ["check_inventory"]
})

# 生成响应 (Agent 会自动调用工具)
response = await claude.generate(
    messages=[LLMMessage(role="user", content="我的背包里有什么?")],
    tools=tools
)

# 检查是否调用了工具
if response.tool_calls:
    for tool_call in response.tool_calls:
        print(f"调用工具: {tool_call.name}")
        print(f"参数: {tool_call.arguments}")
```

---

## 游戏工具

### 可用工具列表

游戏专用的 MCP Server 提供了以下工具:

#### 骰子和检定
- `roll_dice`: 投骰子
- `skill_check`: 技能检定

#### 玩家状态
- `check_status`: 查看角色状态
- `update_player_hp`: 更新生命值
- `update_player_stamina`: 更新体力值

#### 物品管理
- `check_inventory`: 查看背包
- `use_item`: 使用物品
- `add_item`: 添加物品
- `remove_item`: 移除物品

#### 地图探索
- `check_map`: 查看地图
- `check_surroundings`: 环顾四周
- `unlock_location`: 解锁新地点
- `set_location`: 设置玩家位置

#### 任务系统
- `check_quests`: 查看任务列表

#### NPC 交互
- `talk_to_npc`: 与 NPC 对话
- `trade_with_npc`: 与 NPC 交易

#### 标记和奖励
- `set_flag`: 设置游戏标记
- `award_experience`: 奖励经验值

### 使用游戏工具

```python
from claude_agent_sdk import query, ClaudeAgentOptions
from llm.game_tools_mcp import create_game_tools_server, get_game_tool_names
import anyio

async def use_game_tools():
    # 创建游戏工具 MCP Server
    game_tools = create_game_tools_server()

    # 获取所有工具名称
    tool_names = get_game_tool_names()

    # 配置 Agent
    opts = ClaudeAgentOptions(
        mcp_servers={"game-tools": game_tools},
        allowed_tools=tool_names,
        max_turns=5
    )

    # 使用工具
    async for msg in query(
        prompt="帮我投一个20面骰子,然后查看我的背包",
        options=opts
    ):
        print(msg)

anyio.run(use_game_tools)
```

### 工具返回格式

所有游戏工具都返回统一格式:

```python
{
    "content": [
        {
            "type": "text",
            "text": "📦 查看背包"
        }
    ],
    "metadata": {
        "tool_name": "check_inventory",
        "action": "query_inventory"
        # ... 其他元数据
    }
}
```

游戏引擎可以通过 `metadata` 中的 `action` 字段来执行实际操作。

---

## 配置说明

### 全局配置 (config/llm_backend.yaml)

```yaml
# 选择默认后端
backend: "litellm"  # 或 "claude"

# LiteLLM 配置
litellm:
  config_path: "./config/litellm_config.yaml"
  model: "deepseek"
  temperature: 0.7
  max_tokens: 1000

# Claude 配置
claude:
  use_litellm_proxy: true  # 是否使用 LiteLLM 代理
  model: "deepseek"
  temperature: 0.7
  max_tokens: 4096
  allowed_tools: ["Read", "Write", "Bash"]
```

### Agent 配置 (config/llm_agents.yaml)

```yaml
global:
  litellm_proxy_url: "http://0.0.0.0:4000"
  litellm_master_key: ${LITELLM_MASTER_KEY}

agents:
  game_master:
    backend: "claude"
    use_litellm_proxy: true
    model: "deepseek"  # 成本低,中文好
    temperature: 0.8
    max_tokens: 2000
    allowed_tools: ["Read", "Write", "Bash"]

  npc_dialogue:
    backend: "claude"
    use_litellm_proxy: true
    model: "qwen"  # 中文对话优化
    temperature: 0.9
    max_tokens: 1000

  world_generator:
    backend: "claude"
    use_litellm_proxy: true
    model: "claude-sonnet"  # 高质量创作
    temperature: 0.8
    max_tokens: 3000
```

### LiteLLM 模型配置 (config/litellm_config.yaml)

```yaml
model_list:
  - model_name: deepseek
    litellm_params:
      model: openrouter/deepseek/deepseek-v3.1-terminus
      api_key: ${OPENROUTER_API_KEY}

  - model_name: qwen
    litellm_params:
      model: openrouter/qwen/qwen-2.5-72b-instruct
      api_key: ${OPENROUTER_API_KEY}

  - model_name: claude-sonnet
    litellm_params:
      model: openrouter/anthropic/claude-3.5-sonnet
      api_key: ${OPENROUTER_API_KEY}
```

---

## 最佳实践

### 1. 根据任务选择后端

```python
# 简单对话 → LiteLLM + DeepSeek (便宜)
simple_agent = create_backend("litellm", {"model": "deepseek"})

# 需要工具调用 → Claude + LiteLLM Proxy (Agent能力)
tool_agent = create_backend("claude", {
    "use_litellm_proxy": True,
    "model": "deepseek",
    "allowed_tools": ["check_inventory", "roll_dice"]
})

# 高质量创作 → Claude + Claude API (质量高)
creative_agent = create_backend("claude", {
    "use_litellm_proxy": False,
    "model": "claude-sonnet-4-20250514"
})
```

### 2. 使用 Agent 配置系统

```python
# 推荐: 使用配置文件管理多个 Agent
from llm.agent_config import load_agent_backend

gm = load_agent_backend("game_master")
npc = load_agent_backend("npc_dialogue")
world = load_agent_backend("world_generator")

# 优点:
# - 集中管理配置
# - 易于切换模型
# - 成本可控
```

### 3. 合理设置温度

```python
# 逻辑计算、战斗系统 → 低温度 (0.3-0.5)
combat = create_backend("litellm", {
    "model": "deepseek",
    "temperature": 0.5
})

# 正常对话 → 中温度 (0.6-0.8)
dialogue = create_backend("litellm", {
    "model": "qwen",
    "temperature": 0.7
})

# 创意内容、叙事生成 → 高温度 (0.8-1.0)
creative = create_backend("claude", {
    "model": "claude-sonnet",
    "temperature": 0.9
})
```

### 4. 错误处理

```python
from llm.base import LLMError

try:
    response = await gm.generate(messages)
except LLMError as e:
    print(f"LLM 错误: {e}")
    # 降级处理或重试
```

### 5. 监控成本

```python
# 记录每次调用
async def generate_with_logging(backend, messages):
    response = await backend.generate(messages)

    # 从 metadata 获取 token 使用情况
    tokens = response.metadata.get("tokens", {})
    model = response.model

    # 计算成本
    cost_per_1k = {
        "deepseek": 0.0007,
        "qwen": 0.0014,
        "claude-sonnet": 0.011
    }

    total_tokens = tokens.get("total", 0)
    cost = (total_tokens / 1000) * cost_per_1k.get(model, 0)

    print(f"[COST] {model}: ${cost:.4f} ({total_tokens} tokens)")

    return response
```

---

## 相关文档

- [LiteLLM + Claude Agent SDK 完整指南](./LITELLM_AGENT_GUIDE.md)
- [OpenRouter 配置指南](./guides/OPENROUTER_SETUP.md)
- [项目快速参考](./QUICK_REFERENCE.md)

---

**最后更新**: 2025-11-01
**版本**: v1.0
