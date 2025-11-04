"""
DM Agent - 游戏主持人 Agent (LangChain 1.0 实现)
从 Claude Agent SDK 迁移到 LangChain
"""

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, AsyncIterator, List
import os
from .game_tools_langchain import (
    ALL_GAME_TOOLS,
    set_current_session_id,
    state_manager
)


class DMAgentLangChain:
    """游戏主持人 Agent (LangChain 实现)"""

    def __init__(self, model_name: str = None):
        """
        初始化 DM Agent

        Args:
            model_name: 模型名称，默认从环境变量 DEFAULT_MODEL 读取
        """
        # 模型名称映射
        self.model_map = {
            "deepseek": "deepseek/deepseek-chat",
            "claude-sonnet": "anthropic/claude-3.5-sonnet",
            "claude-haiku": "anthropic/claude-3-haiku",
            "gpt-4": "openai/gpt-4-turbo",
            "qwen": "qwen/qwen-2.5-72b-instruct"
        }

        # 获取模型名称
        if model_name is None:
            model_name = os.getenv("DEFAULT_MODEL", "deepseek/deepseek-chat")

        # 映射简写到完整名称
        full_model_name = self.model_map.get(model_name, model_name)

        # 初始化 OpenRouter 模型
        self.model = ChatOpenAI(
            model=full_model_name,
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=0.7,
            max_tokens=4096,
            streaming=True
        )

        # 游戏工具
        self.tools = ALL_GAME_TOOLS

        print(f"[DMAgent] 初始化完成，使用模型: {full_model_name}")

    def _build_system_prompt(self, game_state: Dict[str, Any]) -> str:
        """构建系统提示词"""
        return f"""你是一个单人跑团游戏的游戏主持人（DM）。

世界设定:
{game_state.get('world', {}).get('theme', '奇幻世界')}

当前状态:
- 位置: {game_state.get('world', {}).get('current_location', '未知')}
- 回合数: {game_state.get('turn_number', 0)}

你的职责:
1. 描述场景和环境（生动且富有细节）
2. 管理NPC互动和对话
3. 处理玩家行动的后果
4. 使用工具调用来更新游戏状态:
   - get_player_state: 获取玩家状态
   - add_item: 给予物品
   - update_hp: 修改HP
   - roll_check: 进行技能检定
   - set_location: 移动到新位置
   - create_quest: 创建新任务
   - create_npc: 创建NPC
   - save_game: 保存游戏
5. 提供2-3个有趣的行动建议

重要规则:
- 当玩家行动导致状态变化时，必须调用相应的工具！
- 战斗时要调用 roll_check 和 update_hp
- 获得物品时要调用 add_item
- 移动到新地点时要调用 set_location
- 遇到新NPC时可以调用 create_npc
- 完成关键任务后可以调用 create_quest

叙述风格:
- 使用第二人称("你")与玩家互动
- 描述要生动形象，调动五感
- 适当留白，让玩家有想象空间
- 节奏要张弛有度
"""

    async def process_turn(
        self,
        session_id: str,
        player_action: str,
        game_state: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """处理游戏回合 (流式)

        Args:
            session_id: 会话ID（用于区分不同玩家）
            player_action: 玩家行动
            game_state: 当前游戏状态

        Yields:
            消息事件（narration/tool_call/tool_result/complete）
        """
        # 设置当前会话
        set_current_session_id(session_id)

        # 构建系统提示词
        system_prompt = self._build_system_prompt(game_state)

        # 创建 agent
        agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=system_prompt
        )

        # 构建用户消息
        user_message = f"""玩家行动: {player_action}

请作为DM处理这个行动，使用工具更新游戏状态，并生成精彩的场景描述。
"""

        try:
            # 流式调用
            async for event in agent.astream_events(
                {"messages": [{"role": "user", "content": user_message}]},
                version="v2"
            ):
                event_type = event.get("event")

                # 文本流
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk", {})
                    if hasattr(chunk, "content") and chunk.content:
                        yield {
                            "type": "narration",
                            "content": chunk.content
                        }

                # 工具调用开始
                elif event_type == "on_tool_start":
                    tool_input = event.get("data", {}).get("input", {})
                    yield {
                        "type": "tool_call",
                        "tool": event.get("name"),
                        "input": tool_input
                    }

                # 工具调用结束
                elif event_type == "on_tool_end":
                    tool_output = event.get("data", {}).get("output")
                    yield {
                        "type": "tool_result",
                        "tool": event.get("name"),
                        "output": tool_output
                    }

        except Exception as e:
            yield {
                "type": "error",
                "message": f"处理回合时出错: {str(e)}"
            }

        # 更新回合数
        game_state['turn_number'] = game_state.get('turn_number', 0) + 1

        yield {
            "type": "complete",
            "turn": game_state['turn_number']
        }

    async def process_turn_sync(
        self,
        session_id: str,
        player_action: str,
        game_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理游戏回合（非流式）

        Args:
            session_id: 会话ID
            player_action: 玩家行动
            game_state: 当前游戏状态

        Returns:
            完整的回合结果
        """
        # 设置当前会话
        set_current_session_id(session_id)

        # 构建系统提示词
        system_prompt = self._build_system_prompt(game_state)

        # 创建 agent
        agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=system_prompt
        )

        # 构建用户消息
        user_message = f"""玩家行动: {player_action}

请作为DM处理这个行动，使用工具更新游戏状态，并生成精彩的场景描述。
"""

        # 收集所有消息
        narration_parts = []
        tool_calls = []

        try:
            # 调用 agent (非流式)
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": user_message}]}
            )

            # 解析结果
            messages = result.get("messages", [])
            for message in messages:
                # 提取文本内容
                if hasattr(message, "content") and message.content:
                    narration_parts.append(message.content)

                # 提取工具调用
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_calls.append({
                            "tool": tool_call.get("name"),
                            "input": tool_call.get("args", {})
                        })

        except Exception as e:
            return {
                "narration": f"处理回合时出错: {str(e)}",
                "tool_calls": [],
                "updated_state": game_state,
                "turn": game_state.get('turn_number', 0),
                "error": str(e)
            }

        # 更新回合数
        game_state['turn_number'] = game_state.get('turn_number', 0) + 1

        return {
            "narration": "\n\n".join(narration_parts),
            "tool_calls": tool_calls,
            "updated_state": game_state,
            "turn": game_state['turn_number']
        }

    def get_model_name(self) -> str:
        """获取当前使用的模型名称"""
        return self.model.model_name


# ============= 向后兼容别名 =============

DMAgent = DMAgentLangChain
