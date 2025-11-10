"""
增强版游戏引擎 - 使用 Anthropic SDK 原生 Tool Use
基于 docs/TECHNICAL_IMPLEMENTATION_PLAN.md 第4节设计
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, AsyncIterator
from pydantic import BaseModel
from pathlib import Path

from game.game_tools import GameTools, GameState
try:
    from database.game_state_db import GameStateManager, GameStateCache
except ImportError:
    GameStateManager = None
    GameStateCache = None

# 尝试导入 Anthropic SDK
try:
    from anthropic import Anthropic, AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None
    AsyncAnthropic = None


class GameTurnRequest(BaseModel):
    """游戏回合请求"""
    session_id: str  # 会话ID（用于状态管理）
    player_input: str
    current_state: Optional[GameState] = None  # 可选，如果不提供则从数据库加载


class GameTurnResponse(BaseModel):
    """游戏回合响应"""
    narration: str
    tool_calls: List[Dict[str, Any]] = []
    hints: List[str] = []
    suggestions: List[str] = []
    updated_state: GameState
    metadata: Dict[str, Any] = {}


class GameEngineEnhanced:
    """
    增强版游戏引擎 - 使用 Anthropic SDK Tool Use

    特性:
    1. 原生 Tool Use 支持（不是 JSON prompt）
    2. 自动工具调用循环
    3. 游戏状态持久化（数据库 + 缓存）
    4. 流式输出支持
    """

    def __init__(
        self,
        api_key: str,
        db_path: str,
        model: str = "claude-sonnet-4-20250514",
        base_url: Optional[str] = None
    ):
        """
        Args:
            api_key: Anthropic API Key（或 LiteLLM Master Key）
            db_path: 数据库路径
            model: 模型名称
            base_url: 可选的基础URL（用于 LiteLLM Proxy）
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("需要安装 anthropic: pip install anthropic")

        # 初始化 Anthropic 客户端
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = Anthropic(**client_kwargs)
        self.async_client = AsyncAnthropic(**client_kwargs)
        self.model = model

        # 初始化状态管理器
        self.db_manager = GameStateManager(db_path)
        self.state_cache = GameStateCache(self.db_manager)

    def _build_system_prompt(self, state: GameState) -> str:
        """构建系统提示词"""
        return f"""你是一个单人跑团游戏的游戏主持人（DM）。

**世界观设定**:
- 这是一个奇幻/科幻混合世界
- 玩家可以探索、战斗、解谜、与NPC互动

**当前游戏状态**:
- 位置: {state.player.location}
- 生命值: {state.player.hp}/{state.player.maxHp}
- 体力: {state.player.stamina}/{state.player.maxStamina}
- 金币: {state.player.money}
- 回合数: {state.world.time}

**你的职责**:
1. 根据玩家输入，生成生动的旁白描述（100-300字）
2. 通过工具调用更新游戏状态（生命值、物品、位置等）
3. 保持叙事连贯性和逻辑一致性
4. 提供有趣的挑战和选择

**重要规则**:
- 所有状态变更必须通过工具调用完成
- 不要虚构玩家没有的物品或能力
- 检定失败也要给出有趣的结果
- 旁白要简洁生动，聚焦玩家行动的直接后果

**工具使用指南**:
- 玩家获得物品时，使用 `add_item`
- 玩家受伤/恢复时，使用 `update_hp`
- 玩家移动时，使用 `set_location`
- 需要随机判定时，使用 `roll_check`
- 任务完成时，使用 `complete_quest`
"""

    def _get_or_create_state(self, session_id: str, provided_state: Optional[GameState] = None) -> GameState:
        """获取或创建游戏状态"""
        if provided_state:
            return provided_state

        # 从缓存/数据库加载
        state_dict = self.state_cache.get_state(session_id)
        if state_dict:
            return GameState(**state_dict)

        # 创建新状态
        return self._create_default_state()

    def _create_default_state(self) -> GameState:
        """创建默认游戏状态"""
        from .game_tools import PlayerState, WorldState, GameMap, MapNode

        player = PlayerState(
            hp=100,
            maxHp=100,
            stamina=100,
            maxStamina=100,
            traits=[],
            inventory=[],
            location="start",
            money=10
        )

        world = WorldState(
            time=0,
            flags={},
            discoveredLocations=["start"],
            variables={},
            currentScene=None
        )

        game_map = GameMap(
            nodes=[
                MapNode(
                    id="start",
                    name="起始点",
                    shortDesc="你的冒险从这里开始",
                    discovered=True,
                    locked=False
                )
            ],
            edges=[],
            currentNodeId="start"
        )

        return GameState(
            version="1.0.0",
            player=player,
            world=world,
            quests=[],
            map=game_map,
            log=[]
        )

    async def process_turn(self, request: GameTurnRequest) -> GameTurnResponse:
        """
        处理游戏回合（使用 Anthropic Tool Use）

        流程:
        1. 加载/创建游戏状态
        2. 调用 Claude API with tools
        3. 自动执行工具调用循环
        4. 保存更新后的状态
        5. 返回响应
        """
        # 1. 获取游戏状态
        state = self._get_or_create_state(request.session_id, request.current_state)
        tools_instance = GameTools(state, db_manager=self.db_manager)

        # 2. 获取工具定义
        tool_definitions = GameTools.get_tool_definitions()

        # 3. 构建提示词
        system_prompt = self._build_system_prompt(state)
        user_message = f"玩家行动: {request.player_input}"

        # 4. 初始化对话历史
        messages = [{"role": "user", "content": user_message}]

        # 5. 工具调用循环
        narration_parts = []
        executed_tools = []

        while True:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=messages,
                tools=tool_definitions
            )

            # 收集文本内容
            for block in response.content:
                if block.type == "text":
                    narration_parts.append(block.text)

            # 检查是否有工具调用
            tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

            if not tool_use_blocks:
                # 没有更多工具调用，结束循环
                break

            # 执行工具调用
            tool_results = []
            for tool_block in tool_use_blocks:
                tool_name = tool_block.name
                tool_input = tool_block.input

                # 执行工具
                if hasattr(tools_instance, tool_name):
                    func = getattr(tools_instance, tool_name)
                    try:
                        result = func(**tool_input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_block.id,
                            "content": json.dumps(result, ensure_ascii=False)
                        })

                        executed_tools.append({
                            "name": tool_name,
                            "input": tool_input,
                            "result": result
                        })

                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_block.id,
                            "content": json.dumps({
                                "error": str(e),
                                "success": False
                            }, ensure_ascii=False),
                            "is_error": True
                        })

            # 将助手响应和工具结果添加到对话历史
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            # 检查停止原因
            if response.stop_reason == "end_turn":
                break

        # 6. 更新回合数和日志
        state.world.time += 1
        tools_instance.add_log("player", request.player_input)

        final_narration = "\n\n".join(narration_parts)
        tools_instance.add_log("system", final_narration)  # 🔥 修复：保存完整叙事，不截断

        # 7. 保存状态
        self.state_cache.save_state(request.session_id, state.model_dump())

        # 8. 生成建议
        suggestions = self._generate_suggestions(state)

        # 9. 返回响应
        return GameTurnResponse(
            narration=final_narration,
            tool_calls=executed_tools,
            hints=[],
            suggestions=suggestions,
            updated_state=state,
            metadata={
                "turn": state.world.time,
                "tool_calls_count": len(executed_tools),
                "session_id": request.session_id
            }
        )

    async def process_turn_stream(
        self,
        request: GameTurnRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        流式处理游戏回合

        Yields:
            事件字典，包含 type 和相关数据
        """
        # 1. 获取游戏状态
        state = self._get_or_create_state(request.session_id, request.current_state)
        tools_instance = GameTools(state, db_manager=self.db_manager)

        # 2. 获取工具定义
        tool_definitions = GameTools.get_tool_definitions()

        # 3. 构建提示词
        system_prompt = self._build_system_prompt(state)
        user_message = f"玩家行动: {request.player_input}"

        # 4. 初始化对话历史
        messages = [{"role": "user", "content": user_message}]

        # 5. 流式调用
        executed_tools = []

        async with self.async_client.messages.stream(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=messages,
            tools=tool_definitions
        ) as stream:
            async for event in stream:
                # 文本增量
                if event.type == "content_block_delta":
                    if hasattr(event.delta, "text"):
                        yield {
                            "type": "narration_delta",
                            "text": event.delta.text
                        }

                # 工具调用
                elif event.type == "content_block_start":
                    if hasattr(event.content_block, "type") and event.content_block.type == "tool_use":
                        yield {
                            "type": "tool_use_start",
                            "tool_name": event.content_block.name
                        }

            # 获取最终消息
            message = await stream.get_final_message()

            # 执行工具调用
            for block in message.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    if hasattr(tools_instance, tool_name):
                        func = getattr(tools_instance, tool_name)
                        try:
                            result = func(**tool_input)
                            executed_tools.append({
                                "name": tool_name,
                                "input": tool_input,
                                "result": result
                            })

                            yield {
                                "type": "tool_result",
                                "tool_name": tool_name,
                                "result": result
                            }

                        except Exception as e:
                            yield {
                                "type": "tool_error",
                                "tool_name": tool_name,
                                "error": str(e)
                            }

        # 6. 更新状态
        state.world.time += 1
        tools_instance.add_log("player", request.player_input)

        # 7. 保存状态
        self.state_cache.save_state(request.session_id, state.model_dump())

        # 8. 发送完成事件
        yield {
            "type": "turn_complete",
            "state": state.model_dump(),
            "tool_calls_count": len(executed_tools),
            "turn": state.world.time
        }

    def _generate_suggestions(self, state: GameState) -> List[str]:
        """生成行动建议"""
        suggestions = []

        # 基于位置的建议
        location = next((node for node in state.map.nodes if node.id == state.player.location), None)
        if location:
            suggestions.append(f"探索{location.name}")

        # 基于任务的建议
        active_quests = [q for q in state.quests if q.status == "active"]
        if active_quests:
            suggestions.append(f"查看任务: {active_quests[0].title}")

        # 基于背包的建议
        if state.player.inventory:
            suggestions.append("查看背包")

        # 通用建议
        suggestions.extend(["环顾四周", "与NPC对话"])

        return suggestions[:5]

    def save_game(self, session_id: str, slot_id: int, save_name: str) -> Dict[str, Any]:
        """手动保存游戏"""
        state_dict = self.state_cache.get_state(session_id)
        if not state_dict:
            return {"success": False, "message": "会话不存在"}

        try:
            save_id = self.db_manager.save_game(
                user_id="default_user",
                slot_id=slot_id,
                save_name=save_name,
                game_state=state_dict
            )

            return {
                "success": True,
                "save_id": save_id,
                "message": f"游戏已保存到槽位 {slot_id}"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"保存失败: {str(e)}"
            }

    def load_game(self, session_id: str, save_id: int) -> Dict[str, Any]:
        """加载存档"""
        try:
            save_data = self.db_manager.load_game(save_id)
            if not save_data:
                return {"success": False, "message": "存档不存在"}

            # 加载到会话
            self.state_cache.save_state(session_id, save_data["game_state"])

            return {
                "success": True,
                "save_id": save_id,
                "metadata": save_data["metadata"],
                "message": "存档加载成功"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"加载失败: {str(e)}"
            }
