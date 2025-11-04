# LangChain 1.0 迁移计划

**目标**: 将项目从 Claude Agent SDK + LiteLLM 迁移到 LangChain 1.0 + 直接 OpenRouter 连接

**创建时间**: 2025-11-04

---

## 1. 现状分析

### 1.1 Claude Agent SDK 使用情况

当前项目在以下模块使用 Claude Agent SDK:

1. **游戏工具系统** (`web/backend/agents/game_tools_mcp.py`)
   - 使用 `@tool` 装饰器定义 15 个游戏工具
   - 工具包括: get_player_state, add_item, update_hp, roll_check, set_location
   - 任务系统: create_quest, get_quests, activate_quest, update_quest_objective, complete_quest
   - NPC系统: create_npc, get_npcs, update_npc_relationship, add_npc_memory
   - 存档系统: save_game

2. **DM Agent** (`web/backend/agents/dm_agent.py`)
   - 使用 `query` 和 `ClaudeAgentOptions`
   - 实现游戏主持人逻辑
   - 流式和非流式两种处理模式

3. **LLM 后端** (`web/backend/llm/claude_backend.py`)
   - 使用 Claude Agent SDK 作为后端适配器
   - 通过 LiteLLM Proxy 调用不同模型
   - 支持流式生成和结构化输出

### 1.2 LiteLLM 使用情况

LiteLLM 在以下地方使用:

1. **LiteLLM Backend** (`web/backend/llm/litellm_backend.py`)
   - 通过 LiteLLM Proxy (port 4000) 调用模型
   - 支持多模型路由 (DeepSeek, Claude, GPT-4, Qwen)

2. **配置文件**
   - `config/litellm_config.yaml`: LiteLLM 路由配置
   - `config/litellm_proxy_config.yaml`: Proxy 服务器配置
   - `config/llm_backend.yaml`: 后端选择配置

3. **启动脚本**
   - `scripts/start/start_litellm_proxy.sh`: 启动 Proxy 服务器
   - `scripts/start/start_all_with_agent.sh`: 启动完整系统

4. **依赖**
   - `requirements.txt`: litellm>=1.50.0
   - `requirements.txt`: anthropic>=0.40.0

5. **文档**
   - 大量文档提及 LiteLLM 和 Claude Agent SDK

### 1.3 核心依赖关系

```
游戏工具 (@tool装饰器)
    ↓
DM Agent (query + ClaudeAgentOptions)
    ↓
Claude Backend (claude_agent_sdk)
    ↓
LiteLLM Proxy (port 4000)
    ↓
OpenRouter API
    ↓
DeepSeek / Claude / GPT-4 / Qwen
```

---

## 2. 目标架构

### 2.1 新架构设计

```
游戏工具 (LangChain @tool)
    ↓
DM Agent (create_agent)
    ↓
LangChain ChatOpenAI (base_url=OpenRouter)
    ↓
OpenRouter API
    ↓
DeepSeek / Claude / GPT-4 / Qwen
```

**关键变化**:
- 移除 Claude Agent SDK → LangChain `create_agent`
- 移除 LiteLLM Proxy → 直接使用 OpenRouter
- 移除中间层 → 简化架构

### 2.2 LangChain 1.0 核心 API

根据文档，LangChain 1.0 提供:

1. **Agent 创建** (`create_agent`)
   ```python
   from langchain.agents import create_agent
   from langchain.tools import tool

   agent = create_agent(
       model="openai:gpt-4",  # 或配置为 OpenRouter
       tools=[tool1, tool2],
       system_prompt="你是一个游戏主持人",
       middleware=[...]
   )
   ```

2. **工具定义** (`@tool`)
   ```python
   from langchain.tools import tool

   @tool
   def get_player_state(args: dict) -> dict:
       """获取玩家状态"""
       return {"hp": 100, "gold": 50}
   ```

3. **模型配置** (OpenRouter 集成)
   ```python
   from langchain.chat_models import init_chat_model

   # 方法1: 使用 base_url 参数
   model = init_chat_model(
       model="MODEL_NAME",
       model_provider="openai",
       base_url="https://openrouter.ai/api/v1",
       api_key="YOUR_OPENROUTER_KEY"
   )

   # 方法2: 直接使用 ChatOpenAI
   from langchain_openai import ChatOpenAI

   model = ChatOpenAI(
       model="deepseek/deepseek-chat",
       base_url="https://openrouter.ai/api/v1",
       api_key=os.getenv("OPENROUTER_API_KEY")
   )
   ```

4. **流式输出**
   ```python
   async for event in agent.stream(
       {"messages": [{"role": "user", "content": "探索洞穴"}]}
   ):
       if event["type"] == "text":
           yield event["content"]
   ```

---

## 3. 迁移步骤

### 3.1 Phase 1: 环境准备 (0.5小时)

**任务**:
1. ✅ 安装 LangChain 1.0 依赖
   ```bash
   uv pip install langchain langchain-openai langchain-community
   ```

2. ✅ 更新 `requirements.txt`
   - 移除: `litellm>=1.50.0`, `anthropic>=0.40.0`, `mcp>=1.7.1`
   - 添加: `langchain>=1.0.0`, `langchain-openai>=1.0.0`, `langchain-community>=1.0.0`

3. ✅ 更新 `.env.example`
   - 移除: `ANTHROPIC_API_BASE`, `ANTHROPIC_API_KEY`, `USE_LITELLM_PROXY`, `LITELLM_CONFIG_PATH`
   - 保留: `OPENROUTER_API_KEY`
   - 添加: `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`

### 3.2 Phase 2: 工具系统迁移 (2小时)

**任务**:
1. ✅ 重写 `web/backend/agents/game_tools_langchain.py`
   - 使用 LangChain `@tool` 装饰器
   - 保留所有 15 个工具的功能逻辑
   - 调整参数格式 (从 JSON schema 到 Pydantic 或 dict)

2. ✅ 迁移状态管理器
   - 保留 `GameStateManager` 类
   - 移除 `set_session` 全局变量，改用 context 参数

**代码示例**:
```python
from langchain.tools import tool
from typing import Dict, Any

@tool
def get_player_state() -> Dict[str, Any]:
    """获取玩家当前状态（HP、背包、位置等）"""
    # 从 context 获取 session_id
    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)
    player = state.get('player', {})

    return {
        "hp": player.get('hp', 100),
        "max_hp": player.get('max_hp', 100),
        "stamina": player.get('stamina', 100),
        "location": state.get('world', {}).get('current_location'),
        "inventory": player.get('inventory', []),
        "gold": player.get('gold', 0)
    }

@tool
def add_item(item_id: str, quantity: int = 1) -> Dict[str, Any]:
    """向玩家背包添加物品

    Args:
        item_id: 物品ID
        quantity: 数量 (默认1)
    """
    # 工具逻辑...
    return {"success": True, "message": f"获得了 {quantity} 个 {item_id}"}
```

### 3.3 Phase 3: DM Agent 重构 (3小时)

**任务**:
1. ✅ 重写 `web/backend/agents/dm_agent_langchain.py`
   - 使用 `create_agent` 替换 `query`
   - 配置 OpenRouter 作为模型提供者
   - 实现流式和非流式两种模式

2. ✅ 配置模型连接
   - 创建 OpenRouter ChatModel
   - 配置 DeepSeek 作为默认模型
   - 支持模型切换 (DeepSeek, Claude, GPT-4, Qwen)

**代码示例**:
```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from typing import Dict, Any, AsyncIterator
import os

class DMAgentLangChain:
    """游戏主持人 Agent (LangChain 实现)"""

    def __init__(self, model_name: str = "deepseek/deepseek-chat"):
        # 初始化 OpenRouter 模型
        self.model = ChatOpenAI(
            model=model_name,
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=0.7,
            max_tokens=4096
        )

        # 导入所有游戏工具
        from .game_tools_langchain import ALL_GAME_TOOLS
        self.tools = ALL_GAME_TOOLS

    async def process_turn(
        self,
        session_id: str,
        player_action: str,
        game_state: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """处理游戏回合 (流式)"""

        # 设置当前会话
        set_current_session_id(session_id)

        # 构建系统提示词
        system_prompt = f"""你是一个单人跑团游戏的游戏主持人（DM）。

世界设定:
{game_state.get('world', {}).get('theme', '奇幻世界')}

当前状态:
- 位置: {game_state.get('world', {}).get('current_location', '未知')}
- 回合数: {game_state.get('turn_number', 0)}

你的职责:
1. 描述场景和环境（生动且富有细节）
2. 管理NPC互动和对话
3. 处理玩家行动的后果
4. 使用工具调用来更新游戏状态
5. 提供2-3个有趣的行动建议

重要: 当玩家行动导致状态变化时，必须调用相应的工具！
"""

        # 创建 agent
        agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=system_prompt
        )

        # 流式调用
        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": f"玩家行动: {player_action}"}]}
        ):
            # 根据事件类型分发
            if event["event"] == "on_chat_model_stream":
                yield {
                    "type": "narration",
                    "content": event["data"]["chunk"].content
                }
            elif event["event"] == "on_tool_start":
                yield {
                    "type": "tool_call",
                    "tool": event["name"],
                    "input": event["data"]["input"]
                }
            elif event["event"] == "on_tool_end":
                yield {
                    "type": "tool_result",
                    "tool": event["name"],
                    "output": event["data"]["output"]
                }
```

### 3.4 Phase 4: LLM 后端迁移 (2小时)

**任务**:
1. ✅ 创建 `web/backend/llm/langchain_backend.py`
   - 实现统一的 `LLMBackend` 接口
   - 使用 LangChain ChatOpenAI 连接 OpenRouter
   - 支持多模型配置

2. ✅ 更新 `web/backend/llm/__init__.py`
   - 移除 `LiteLLMBackend` 和 `ClaudeBackend`
   - 添加 `LangChainBackend`
   - 更新后端工厂函数

**代码示例**:
```python
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from typing import List, Optional, AsyncIterator
import os

class LangChainBackend(LLMBackend):
    """LangChain 后端 (通过 OpenRouter)"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # 模型映射
        self.model_map = {
            "deepseek": "deepseek/deepseek-chat",
            "claude-sonnet": "anthropic/claude-3.5-sonnet",
            "gpt-4": "openai/gpt-4-turbo",
            "qwen": "qwen/qwen-2.5-72b-instruct"
        }

        # 默认模型
        default_model_key = self.config.get("model", "deepseek")
        model_name = self.model_map.get(default_model_key, default_model_key)

        # 初始化 ChatOpenAI
        self.model = ChatOpenAI(
            model=model_name,
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens", 4096)
        )

    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        **kwargs
    ) -> LLMResponse:
        """生成文本响应"""
        # 转换消息格式
        lc_messages = []
        for msg in messages:
            if msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))

        # 调用模型
        if tools:
            model_with_tools = self.model.bind_tools(tools)
            response = await model_with_tools.ainvoke(lc_messages)
        else:
            response = await self.model.ainvoke(lc_messages)

        return LLMResponse(
            content=response.content,
            tool_calls=response.tool_calls if hasattr(response, 'tool_calls') else [],
            metadata={"model": self.model.model_name}
        )

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        **kwargs
    ) -> AsyncIterator[str]:
        """流式生成"""
        # 转换消息
        lc_messages = [HumanMessage(content=msg.content) for msg in messages if msg.role != "system"]

        # 流式调用
        async for chunk in self.model.astream(lc_messages):
            if hasattr(chunk, 'content'):
                yield chunk.content
```

### 3.5 Phase 5: 清理工作 (1.5小时)

**任务**:
1. ✅ 删除 LiteLLM 相关代码
   - `web/backend/llm/litellm_backend.py`
   - `web/backend/llm/claude_backend.py`
   - `web/backend/agents/mcp_servers.py`
   - `src/llm/litellm_client.py`

2. ✅ 删除配置文件
   - `config/litellm_config.yaml`
   - `config/litellm_proxy_config.yaml`
   - 更新 `config/llm_backend.yaml` (移除 litellm/claude 选项)

3. ✅ 删除启动脚本
   - `scripts/start/start_litellm_proxy.sh`
   - 更新 `scripts/start/start_all_with_agent.sh` (移除 proxy 启动)

4. ✅ 更新依赖
   - 从 `requirements.txt` 移除 litellm, anthropic, mcp

### 3.6 Phase 6: 文档更新 (1.5小时)

**任务**:
1. ✅ 删除 Claude Agent SDK 文档
   - `docs/CLAUDE_AGENT_SDK_INTEGRATION.md`
   - `docs/setup/CLAUDE_AGENT_SDK_SETUP.md`
   - `docs/implementation/CLAUDE_AGENT_SDK_IMPLEMENTATION.md`
   - `docs/reference/CLAUDE_AGENT_SDK_EVALUATION.md`
   - `docs/guides/AGENT_SDK_WITH_DEEPSEEK.md`
   - `QUICKSTART_AGENT_SDK.md`

2. ✅ 删除 LiteLLM 文档
   - `docs/LITELLM_PROXY_MIGRATION_COMPLETE.md`
   - `docs/setup/LITELLM_PROXY_MIGRATION_COMPLETE.md`
   - `docs/setup/LITELLM_PROXY_SETUP.md`
   - `docs/operations/LITELLM_AGENT_GUIDE.md`
   - `docs/operations/LLM_BACKEND_GUIDE.md`
   - `docs/operations/LLM_BACKEND_USAGE.md`
   - `docs/implementation/LLM_BACKEND_INTEGRATION_COMPLETE.md`

3. ✅ 创建 LangChain 文档
   - `docs/setup/LANGCHAIN_SETUP.md`: 安装和配置指南
   - `docs/implementation/LANGCHAIN_AGENT_IMPLEMENTATION.md`: Agent 实现细节
   - `docs/operations/LANGCHAIN_USAGE_GUIDE.md`: 使用指南
   - `docs/reference/LANGCHAIN_QUICK_REFERENCE.md`: 快速参考

4. ✅ 更新核心文档
   - `CLAUDE.md`: 更新技术栈说明
   - `README.md`: 更新依赖和启动说明
   - `docs/TECHNICAL_IMPLEMENTATION_PLAN.md`: 更新架构设计

### 3.7 Phase 7: 测试验证 (2小时)

**任务**:
1. ✅ 更新单元测试
   - `tests/integration/test_claude_agent_sdk.py` → `test_langchain_agent.py`
   - 测试所有 15 个游戏工具
   - 测试 DM Agent 流式和非流式模式

2. ✅ 端到端测试
   - 测试完整的游戏流程
   - 验证工具调用正确性
   - 验证状态管理

3. ✅ 性能测试
   - 对比迁移前后的响应速度
   - 验证 OpenRouter 直连是否更快

**测试脚本示例**:
```python
import pytest
from web.backend.agents.dm_agent_langchain import DMAgentLangChain

@pytest.mark.asyncio
async def test_dm_agent_process_turn():
    """测试 DM Agent 处理回合"""
    agent = DMAgentLangChain()

    game_state = {
        "world": {"theme": "奇幻森林", "current_location": "村庄"},
        "turn_number": 1
    }

    # 非流式测试
    result = await agent.process_turn_sync(
        session_id="test_session",
        player_action="我想去森林探险",
        game_state=game_state
    )

    assert "narration" in result
    assert len(result["narration"]) > 0
    print(f"叙述: {result['narration']}")

@pytest.mark.asyncio
async def test_game_tools():
    """测试游戏工具"""
    from web.backend.agents.game_tools_langchain import (
        get_player_state,
        add_item,
        update_hp
    )

    # 测试获取状态
    state = await get_player_state.ainvoke({})
    assert "hp" in state
    assert "inventory" in state

    # 测试添加物品
    result = await add_item.ainvoke({"item_id": "剑", "quantity": 1})
    assert result["success"] is True

    # 测试更新HP
    result = await update_hp.ainvoke({"change": -10, "reason": "战斗受伤"})
    assert result["new_hp"] < result["old_hp"]
```

---

## 4. 风险和挑战

### 4.1 技术风险

1. **工具调用格式差异**
   - Claude Agent SDK 使用 JSON schema
   - LangChain 可能需要 Pydantic 模型
   - **缓解**: 使用适配器转换格式

2. **流式输出差异**
   - Claude Agent SDK 的 `query` 返回异步迭代器
   - LangChain 使用 `astream_events`
   - **缓解**: 封装统一接口

3. **状态管理**
   - Claude Agent SDK 使用全局 `current_session_id`
   - LangChain 可能需要 context 参数
   - **缓解**: 使用 Context 或 ToolRuntime

### 4.2 兼容性风险

1. **OpenRouter 限制**
   - 某些模型可能不支持工具调用
   - **缓解**: 测试所有目标模型的工具支持

2. **性能问题**
   - 移除 LiteLLM 可能影响缓存
   - **缓解**: 实现客户端缓存

### 4.3 业务风险

1. **功能回归**
   - 迁移可能丢失某些功能
   - **缓解**: 完整的测试覆盖

2. **用户影响**
   - 迁移期间服务中断
   - **缓解**: 分阶段迁移，保留回滚选项

---

## 5. 时间估算

| 阶段 | 任务 | 预估时间 |
|-----|-----|---------|
| Phase 1 | 环境准备 | 0.5h |
| Phase 2 | 工具系统迁移 | 2h |
| Phase 3 | DM Agent 重构 | 3h |
| Phase 4 | LLM 后端迁移 | 2h |
| Phase 5 | 清理工作 | 1.5h |
| Phase 6 | 文档更新 | 1.5h |
| Phase 7 | 测试验证 | 2h |
| **总计** | | **12.5h** |

**缓冲时间**: 2.5h
**总预估**: 15h (约2个工作日)

---

## 6. 回滚计划

如果迁移失败，可以通过以下步骤回滚:

1. ✅ 恢复 Git 提交
   ```bash
   git reset --hard HEAD~1
   ```

2. ✅ 恢复依赖
   ```bash
   uv pip install litellm anthropic mcp
   ```

3. ✅ 重启服务
   ```bash
   ./scripts/start/start_all_with_agent.sh
   ```

---

## 7. 成功标准

迁移成功的标准:

1. ✅ **功能完整**: 所有 15 个游戏工具正常工作
2. ✅ **性能稳定**: 响应时间 < 3秒
3. ✅ **测试通过**: 所有单元测试和集成测试通过
4. ✅ **文档完善**: 新文档清晰易懂
5. ✅ **无依赖冲突**: requirements.txt 干净整洁
6. ✅ **代码简化**: 移除 > 2000 行冗余代码

---

## 8. 下一步行动

**现在开始执行迁移吗？请确认以下事项:**

1. ✅ 已备份当前代码 (git commit)
2. ✅ 已获取 OPENROUTER_API_KEY
3. ✅ 已阅读并理解迁移计划
4. ✅ 预留足够的时间 (2个工作日)

**如果以上全部确认，请回复 "开始迁移"，我将立即开始执行 Phase 1。**
