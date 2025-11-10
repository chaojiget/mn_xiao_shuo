"""
DM Agent - 游戏主持人 Agent
使用 Claude Agent SDK 的 query 和 ClaudeAgentOptions
基于 docs/TECHNICAL_IMPLEMENTATION_PLAN.md 第4.3节设计
"""

from typing import Any, AsyncIterator, Dict

from claude_agent_sdk import ClaudeAgentOptions, query

from .game_tools_mcp import set_session
from .mcp_servers import get_game_server


class DMAgent:
    """游戏主持人 Agent"""

    def __init__(self):
        # 获取 MCP Server
        self.game_server = get_game_server()

        # 配置 Agent 选项
        self.base_options = ClaudeAgentOptions(
            mcp_servers={"game": self.game_server},
            allowed_tools=[
                "mcp__game__get_player_state",
                "mcp__game__add_item",
                "mcp__game__update_hp",
                "mcp__game__roll_check",
                "mcp__game__set_location",
                "mcp__game__create_quest",
                "mcp__game__save_game",
            ],
        )

    async def process_turn(
        self, session_id: str, player_action: str, game_state: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """处理游戏回合

        Args:
            session_id: 会话ID（用于区分不同玩家）
            player_action: 玩家行动
            game_state: 当前游戏状态

        Yields:
            消息事件（narration/tool_call/complete）
        """
        # 设置当前会话
        set_session(session_id)

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
4. 使用工具调用来更新游戏状态:
   - get_player_state: 获取玩家状态
   - add_item: 给予物品
   - update_hp: 修改HP
   - roll_check: 进行技能检定
   - set_location: 移动到新位置
   - create_quest: 创建新任务
   - save_game: 保存游戏
5. 提供2-3个有趣的行动建议

重要: 当玩家行动导致状态变化时，必须调用相应的工具！
"""

        # 构建提示词
        prompt = f"""玩家行动: {player_action}

请作为DM处理这个行动，使用工具更新游戏状态，并生成精彩的场景描述。
"""

        # 配置选项
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            mcp_servers={"game": self.game_server},
            allowed_tools=self.base_options.allowed_tools,
        )

        # 流式返回
        async for message in query(prompt=prompt, options=options):
            yield message

    async def process_turn_sync(
        self, session_id: str, player_action: str, game_state: Dict[str, Any]
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
        set_session(session_id)

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

        # 构建提示词
        prompt = f"""玩家行动: {player_action}

请作为DM处理这个行动，使用工具更新游戏状态，并生成精彩的场景描述。
"""

        # 配置选项
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            mcp_servers={"game": self.game_server},
            allowed_tools=self.base_options.allowed_tools,
        )

        # 收集所有消息
        narration_parts = []
        tool_calls = []

        async for message in query(prompt=prompt, options=options):
            # 解析消息类型
            if hasattr(message, "type"):
                if message.type == "text":
                    narration_parts.append(message.text)
                elif message.type == "tool_use":
                    tool_calls.append({"tool": message.name, "input": message.input})
                elif message.type == "tool_result":
                    # 工具结果
                    pass

        # 更新回合数
        game_state["turn_number"] = game_state.get("turn_number", 0) + 1

        return {
            "narration": "\n\n".join(narration_parts),
            "tool_calls": tool_calls,
            "updated_state": game_state,
            "turn": game_state["turn_number"],
        }
