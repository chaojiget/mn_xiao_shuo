# LangChain 1.0 快速开始指南

本项目已从 Claude Agent SDK + LiteLLM 迁移到 **LangChain 1.0 + OpenRouter**。

---

## 🎯 新架构概览

```
游戏工具 (LangChain @tool)
    ↓
DM Agent (create_agent)
    ↓
LangChain ChatOpenAI
    ↓
OpenRouter API
    ↓
DeepSeek/Claude/GPT-4/Qwen
```

**优势**:
- ✅ 移除 LiteLLM Proxy 中间层，降低延迟
- ✅ 直连 OpenRouter，简化架构
- ✅ 使用 LangChain 标准 API，更易维护
- ✅ 支持流式生成和工具调用

---

## 📦 安装依赖

```bash
# 使用 uv 安装
uv pip install -r requirements.txt

# 主要依赖:
# - langchain>=1.0.0
# - langchain-openai>=1.0.0
# - langchain-community>=1.0.0
# - openai>=1.50.0 (用于 OpenRouter 连接)
```

---

## ⚙️ 环境配置

编辑 `.env` 文件:

```bash
# OpenRouter API Key (必需)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# OpenRouter Base URL (可选，默认为下面的值)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# 默认模型 (可选，默认为 deepseek/deepseek-chat)
DEFAULT_MODEL=deepseek/deepseek-chat

# 数据库配置
DATABASE_URL=sqlite:///./data/sqlite/novel.db
```

**支持的模型**:
- `deepseek/deepseek-chat` - DeepSeek (默认，高性价比)
- `anthropic/claude-3.5-sonnet` - Claude 3.5 Sonnet
- `anthropic/claude-3-haiku` - Claude 3 Haiku
- `openai/gpt-4-turbo` - GPT-4 Turbo
- `qwen/qwen-2.5-72b-instruct` - Qwen 2.5

---

## 🚀 启动服务

### 方法1: 一键启动（推荐）

```bash
./scripts/start/start_all_with_agent.sh
```

这会启动:
- FastAPI 后端 (端口 8000)
- Next.js 前端 (端口 3000)

访问:
- 游戏界面: http://localhost:3000/game/play
- API 文档: http://localhost:8000/docs

### 方法2: 手动启动

```bash
# 启动后端
cd web/backend
uv run uvicorn main:app --reload --port 8000

# 启动前端（新终端）
cd web/frontend
npm run dev
```

---

## 🎮 核心组件

### 1. 游戏工具 (`web/backend/agents/game_tools_langchain.py`)

15个 LangChain 工具:

**核心工具**:
- `get_player_state()` - 获取玩家状态
- `add_item(item_id, quantity)` - 添加物品
- `update_hp(change, reason)` - 更新HP
- `roll_check(skill, dc, modifier, advantage)` - d20技能检定
- `set_location(location_id, description)` - 移动位置
- `save_game(slot_id, save_name)` - 保存游戏

**任务系统**:
- `create_quest(...)` - 创建任务
- `get_quests(status)` - 获取任务列表
- `activate_quest(quest_id)` - 激活任务
- `update_quest_objective(...)` - 更新任务进度
- `complete_quest(quest_id)` - 完成任务

**NPC系统**:
- `create_npc(...)` - 创建NPC
- `get_npcs(location, status)` - 获取NPC列表
- `update_npc_relationship(...)` - 更新NPC关系
- `add_npc_memory(...)` - 添加NPC记忆

### 2. DM Agent (`web/backend/agents/dm_agent_langchain.py`)

使用 LangChain `create_agent`:

```python
from web.backend.agents.dm_agent_langchain import DMAgentLangChain

# 初始化 Agent
agent = DMAgentLangChain(model_name="deepseek/deepseek-chat")

# 处理游戏回合（流式）
async for event in agent.process_turn(
    session_id="session_123",
    player_action="我探索洞穴",
    game_state=current_game_state
):
    if event["type"] == "narration":
        print(event["content"])
    elif event["type"] == "tool_call":
        print(f"调用工具: {event['tool']}")
```

### 3. LLM 后端 (`web/backend/llm/langchain_backend.py`)

统一的 LLM 接口:

```python
from web.backend.llm import LangChainBackend, LLMMessage

# 初始化后端
backend = LangChainBackend(config={
    "model": "deepseek/deepseek-chat",
    "temperature": 0.7
})

# 生成文本
response = await backend.generate(
    messages=[
        LLMMessage(role="user", content="讲个故事")
    ]
)

# 流式生成
async for chunk in backend.generate_stream(messages):
    print(chunk, end="")
```

---

## 🧪 测试

```bash
# 运行所有测试
uv run pytest tests/

# 测试 LangChain Agent
uv run pytest tests/integration/test_langchain_agent.py

# 测试游戏工具
uv run pytest tests/integration/test_game_tools.py
```

---

## 📚 相关文档

- **迁移计划**: `docs/implementation/LANGCHAIN_MIGRATION_PLAN.md`
- **游戏功能**: `docs/features/GAME_FEATURES.md`
- **API 文档**: `docs/implementation/PHASE2_API_ENDPOINTS.md`
- **故障排查**: `docs/troubleshooting/TROUBLESHOOTING.md`

---

## 🔧 常见问题

### Q: 如何切换模型？

**方法1**: 修改 `.env` 文件
```bash
DEFAULT_MODEL=anthropic/claude-3.5-sonnet
```

**方法2**: 代码中指定
```python
agent = DMAgentLangChain(model_name="openai/gpt-4-turbo")
```

### Q: 如何查看日志？

```bash
# 后端日志
tail -f logs/backend.log

# 前端日志
tail -f logs/frontend.log
```

### Q: 工具调用失败怎么办？

检查:
1. 模型是否支持工具调用（DeepSeek/Claude/GPT-4都支持）
2. OpenRouter API Key 是否有效
3. 查看后端日志中的错误信息

### Q: 如何添加新工具？

在 `web/backend/agents/game_tools_langchain.py` 中添加:

```python
from langchain.tools import tool

@tool
def my_new_tool(arg1: str, arg2: int) -> dict:
    """工具描述

    Args:
        arg1: 参数1说明
        arg2: 参数2说明

    Returns:
        结果字典
    """
    # 工具逻辑
    return {"success": True}

# 添加到工具列表
ALL_GAME_TOOLS.append(my_new_tool)
```

---

## 🆘 获取帮助

- 查看日志: `logs/backend.log`
- API 文档: http://localhost:8000/docs
- 故障排查: `docs/troubleshooting/TROUBLESHOOTING.md`
- GitHub Issues: (项目仓库地址)

---

**祝你使用愉快！🎉**
