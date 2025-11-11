"""
DM Agent with LangGraph Memory (可选版本)

使用 LangGraph Checkpoint 实现长期记忆的 DM Agent
适合需要高级记忆管理的场景
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Dict

from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.store.memory import InMemoryStore
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)


# ============= 数据结构 =============


@dataclass
class DMContext:
    """DM Agent 上下文"""

    session_id: str
    user_id: str = "default_user"


class PlayerMemory(TypedDict):
    """玩家记忆（长期保存）"""

    name: str
    preferences: str
    important_events: list


class GameMemory(TypedDict):
    """游戏记忆（重要事件）"""

    event: str
    location: str
    npc_involved: str
    emotional_impact: int  # -10 到 +10


# ============= 记忆工具 =============


@tool
def save_player_memory(memory: PlayerMemory, runtime: ToolRuntime[DMContext]) -> str:
    """保存玩家的长期记忆（偏好、习惯等）

    Args:
        memory: 玩家记忆信息
        runtime: 运行时环境

    Returns:
        成功消息
    """
    store = runtime.store
    user_id = runtime.context.user_id

    # 保存到 store（跨会话持久化）
    store.put(("player_memories",), user_id, memory)

    logger.info(f"💾 已保存玩家记忆: {user_id}")
    return f"✅ 已保存玩家记忆: {memory.get('name', '未知玩家')}"


@tool
def recall_player_memory(runtime: ToolRuntime[DMContext]) -> str:
    """回忆玩家的长期记忆

    Returns:
        玩家记忆字符串
    """
    store = runtime.store
    user_id = runtime.context.user_id

    item = store.get(("player_memories",), user_id)

    if item:
        memory = item.value
        return (
            f"玩家记忆:\n"
            f"  姓名: {memory.get('name', '未知')}\n"
            f"  偏好: {memory.get('preferences', '未设置')}\n"
            f"  重要事件: {', '.join(memory.get('important_events', []))}"
        )
    else:
        return "❌ 没有找到玩家记忆"


@tool
def save_game_memory(memory: GameMemory, runtime: ToolRuntime[DMContext]) -> str:
    """保存重要的游戏事件记忆

    Args:
        memory: 游戏记忆
        runtime: 运行时环境

    Returns:
        成功消息
    """
    store = runtime.store
    session_id = runtime.context.session_id

    import time

    memory_id = f"event_{int(time.time())}"

    # 保存到该会话的记忆空间
    store.put(("game_memories", session_id), memory_id, memory)

    logger.info(f"💾 已保存游戏记忆: {memory['event']}")
    return f"✅ 已记录事件: {memory['event']}"


@tool
def recall_game_memories(limit: int = 5, runtime: ToolRuntime[DMContext] = None) -> str:
    """回忆最近的重要游戏事件

    Args:
        limit: 返回的记忆数量
        runtime: 运行时环境

    Returns:
        游戏记忆列表
    """
    store = runtime.store
    session_id = runtime.context.session_id

    # 搜索该会话的所有记忆
    items = store.search(("game_memories", session_id))

    if not items:
        return "❌ 没有记录的游戏记忆"

    recent = items[:limit]
    result = f"📚 最近 {len(recent)} 个重要事件:\n"

    for item in recent:
        mem = item.value
        result += f"  - {mem['event']} (在 {mem['location']})\n"

    return result


# ============= DM Agent with Memory =============


class DMAgentWithMemory:
    """带长期记忆的 DM Agent

    特性：
    - 使用 LangGraph Checkpoint 自动保存对话历史
    - 使用 Store 保存长期记忆（玩家偏好、重要事件）
    - 支持跨会话记忆恢复

    使用示例：
        async with DMAgentWithMemory() as dm:
            async for event in dm.process_turn(
                session_id="session_123",
                user_id="user_456",
                player_action="我向酒馆老板娘打听消息"
            ):
                logger.info(event)
    """

    def __init__(
        self, checkpoint_db: str = "data/checkpoints/dm_memory.db", model_name: str = None
    ):
        """初始化 DM Agent

        Args:
            checkpoint_db: Checkpoint 数据库路径
            model_name: 模型名称
        """
        self.checkpoint_db = checkpoint_db
        Path(checkpoint_db).parent.mkdir(parents=True, exist_ok=True)

        # 模型配置
        self.model_map = {
            "deepseek": "deepseek/deepseek-v3.1-terminus",
            "claude-sonnet": "anthropic/claude-3.5-sonnet",
            "claude-haiku": "anthropic/claude-3-haiku",
        }

        if model_name is None:
            from config.settings import settings
            model_name = settings.default_model

        full_model_name = self.model_map.get(model_name, model_name)

        from config.settings import settings
        self.model = ChatOpenAI(
            model=full_model_name,
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            temperature=settings.llm_temperature,
            streaming=True,
        )

        # Store（长期记忆）
        self.store = InMemoryStore()

        # Tools
        self.tools = [
            save_player_memory,
            recall_player_memory,
            save_game_memory,
            recall_game_memories,
        ]

        # Checkpointer（稍后在 async with 中初始化）
        self.checkpointer = None
        self._checkpointer_ctx = None

        logger.info(f"✅ DMAgentWithMemory 初始化")
        logger.info(f"  模型: {full_model_name}")
        logger.info(f"  Checkpoint DB: {checkpoint_db}")
        logger.info(f"  工具数量: {len(self.tools)}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 创建 checkpointer
        self._checkpointer_ctx = AsyncSqliteSaver.from_conn_string(self.checkpoint_db)
        self.checkpointer = await self._checkpointer_ctx.__aenter__()
        logger.info("✅ Checkpoint 连接已建立")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._checkpointer_ctx:
            await self._checkpointer_ctx.__aexit__(exc_type, exc_val, exc_tb)
            logger.info("✅ Checkpoint 连接已关闭")

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一个单人跑团游戏的游戏主持人（DM）。

你的职责：
1. 描述场景和环境（生动且富有细节）
2. 管理NPC互动和对话
3. 处理玩家行动的后果
4. 使用工具管理长期记忆：
   - save_player_memory: 保存玩家的偏好和习惯
   - recall_player_memory: 回忆玩家的信息
   - save_game_memory: 记录重要的游戏事件
   - recall_game_memories: 回忆重要事件

重要规则：
1. 对话历史会自动保存（无需担心）
2. 重要事件应该调用 save_game_memory 保存
3. 首次遇到玩家时，调用 recall_player_memory 了解玩家
4. 玩家透露重要信息时，调用 save_player_memory 保存

叙述风格：
- 使用第二人称("你")与玩家互动
- 描述要生动形象，调动五感
- 适当留白，让玩家有想象空间
"""

    async def process_turn(
        self, session_id: str, player_action: str, user_id: str = "default_user"
    ) -> AsyncIterator[Dict[str, Any]]:
        """处理游戏回合

        Args:
            session_id: 会话ID
            player_action: 玩家行动
            user_id: 用户ID

        Yields:
            事件字典
        """
        logger.info(f"🎲 处理回合: session={session_id}, user={user_id}")

        # 创建 Agent
        agent = create_agent(
            model=self.model,
            tools=self.tools,
            checkpointer=self.checkpointer,  # 👈 对话历史自动保存
            store=self.store,  # 👈 长期记忆
            context_schema=DMContext,
            system_prompt=self._build_system_prompt(),
        )

        # 配置
        context = DMContext(session_id=session_id, user_id=user_id)
        config = {"configurable": {"thread_id": session_id}}

        # 流式调用
        try:
            async for event in agent.astream_events(
                {"messages": [{"role": "user", "content": player_action}]},
                config=config,
                context=context,
                version="v2",
            ):
                event_type = event.get("event")

                # 文本流
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk", {})
                    if hasattr(chunk, "content") and chunk.content:
                        yield {"type": "narration", "content": chunk.content}

                # 工具调用
                elif event_type == "on_tool_start":
                    tool_name = event.get("name")
                    tool_input = event.get("data", {}).get("input", {})
                    logger.info(f"🔧 工具调用: {tool_name}")
                    yield {"type": "tool_call", "tool": tool_name, "input": tool_input}

                # 工具结束
                elif event_type == "on_tool_end":
                    tool_name = event.get("name")
                    tool_output = event.get("data", {}).get("output")
                    logger.info(f"✅ 工具完成: {tool_name}")
                    yield {"type": "tool_result", "tool": tool_name, "output": tool_output}

        except Exception as e:
            logger.error(f"❌ 处理回合出错: {e}")
            yield {"type": "error", "message": str(e)}

        yield {"type": "complete"}

    async def get_conversation_history(self, session_id: str) -> list:
        """获取会话的对话历史

        Args:
            session_id: 会话ID

        Returns:
            消息列表
        """
        config = {"configurable": {"thread_id": session_id}}
        state = await self.checkpointer.aget(config)

        if state and isinstance(state, dict):
            return state.get("messages", [])
        else:
            return []
