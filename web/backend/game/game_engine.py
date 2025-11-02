"""
游戏引擎 - 处理游戏回合，集成LLM与工具调用
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, AsyncIterator
from pydantic import BaseModel

from .game_tools import GameTools, GameState, PlayerState, WorldState, GameMap, RollCheckParams
from .quests import QuestEngine

# 世界系统导入（可选）
try:
    from ..database.world_db import WorldDatabase
    from ..services.scene_refinement import SceneRefinement
    WORLD_SYSTEM_AVAILABLE = True
except ImportError:
    WORLD_SYSTEM_AVAILABLE = False
    WorldDatabase = None
    SceneRefinement = None


class GameTurnRequest(BaseModel):
    """游戏回合请求"""
    playerInput: str
    currentState: GameState


class GameTurnResponse(BaseModel):
    """游戏回合响应"""
    narration: str
    actions: List[Dict[str, Any]] = []
    hints: List[str] = []
    suggestions: List[str] = []
    metadata: Dict[str, Any] = {}


class GameEngine:
    """游戏引擎：协调LLM、工具、状态管理"""

    def __init__(self, llm_backend, quest_data_path: Optional[str] = None, db_path: Optional[str] = None):
        """
        Args:
            llm_backend: LLM后端实例（支持LiteLLM或Claude）
            quest_data_path: 任务配置文件目录路径
            db_path: 数据库路径（用于世界系统）
        """
        self.llm_backend = llm_backend

        # 初始化任务引擎
        if quest_data_path is None:
            # 默认路径
            project_root = Path(__file__).parent.parent.parent
            quest_data_path = str(project_root / "data" / "quests")

        self.quest_engine = QuestEngine(quest_data_path)

        # 初始化世界系统（如果可用）
        self.world_db = None
        self.scene_refinement = None
        if WORLD_SYSTEM_AVAILABLE:
            try:
                self.world_db = WorldDatabase(db_path)
                self.scene_refinement = SceneRefinement(llm_backend, self.world_db)
                print("✅ 世界系统已启用")
            except Exception as e:
                print(f"⚠️  世界系统初始化失败: {e}")
                self.world_db = None
                self.scene_refinement = None

    def _build_system_prompt(self, state: GameState) -> str:
        """构建系统提示词"""
        return f"""你是一个单人跑团游戏的主持人（Game Master, GM）。

**世界观设定**：
- 这是一个科幻/奇幻混合世界
- 玩家可以探索、战斗、解谜、与NPC互动
- 世界遵循基本的物理和魔法规则

**你的职责**：
1. 根据玩家输入，生成沉浸式的旁白描述
2. 通过工具调用更新游戏状态（生命值、物品、位置等）
3. 保持叙事连贯性和逻辑一致性
4. 提供有趣的挑战和选择

**输出格式要求**：
你必须返回JSON格式，包含以下字段：
{{
  "narration": "沉浸式的旁白文本",
  "tool_calls": [
    {{"name": "工具名", "arguments": {{...}}}}
  ],
  "hints": ["可选的提示信息"],
  "suggestions": ["玩家可能的下一步行动建议（3-5个）"]
}}

**重要规则**：
- 所有状态变更必须通过工具调用完成
- 不要虚构玩家没有的物品或能力
- 检定失败也要给出有趣的结果
- 保持旁白简洁生动（100-300字为宜）

**当前游戏状态**：
- 位置：{state.player.location}
- 生命值：{state.player.hp}/{state.player.maxHp}
- 体力：{state.player.stamina}/{state.player.maxStamina}
- 背包物品数：{len(state.player.inventory)}
- 当前回合：{state.world.time}
"""

    def _build_context_prompt(self, state: GameState) -> str:
        """构建上下文提示"""
        # 获取当前位置信息
        location_info = "未知"
        for node in state.map.nodes:
            if node.id == state.player.location:
                location_info = f"{node.name} - {node.shortDesc}"
                break

        # 获取活跃任务
        active_quests = [q for q in state.quests if q.status == "active"]
        quests_info = "\n".join([f"  - {q.title}: {q.description}" for q in active_quests[:3]])

        # 获取背包摘要
        inventory_info = "\n".join([f"  - {item.name} x{item.quantity}" for item in state.player.inventory[:5]])

        # 获取近期日志
        recent_logs = state.log[-5:] if state.log else []
        logs_info = "\n".join([f"  [{entry.actor}] {entry.text[:50]}..." for entry in recent_logs])

        return f"""
**当前情境**：
位置：{location_info}

活跃任务：
{quests_info or "  无"}

背包物品：
{inventory_info or "  空"}

最近发生：
{logs_info or "  无"}
"""

    async def _enter_location(self, location_id: str, turn: int, character_state: Dict) -> Dict[str, Any]:
        """
        玩家进入地点时的处理逻辑

        Args:
            location_id: 地点ID
            turn: 当前回合数
            character_state: 角色状态（用于提取可供性）

        Returns:
            包含narrative_text（叙事文本）和affordances（可供性）的字典
        """
        if not self.world_db or not self.scene_refinement:
            # 世界系统不可用，返回空结果
            return {
                "narrative_text": "",
                "affordances": []
            }

        try:
            # 1. 获取地点信息
            location = self.world_db.get_location(location_id)
            if not location:
                return {"narrative_text": "", "affordances": []}

            # 2. 检查是否需要细化
            if location.detail_level < 2:
                # 触发4-Pass细化流水线
                refine_result = await self.scene_refinement.refine_location(
                    request={
                        "location_id": location_id,
                        "turn": turn,
                        "target_detail_level": 2,
                        "passes": ["structure", "sensory", "affordance", "cinematic"]
                    },
                    world_style=self._get_world_style(location)
                )

                # 3. 更新访问记录
                location.visit_count = (location.visit_count or 0) + 1
                location.last_visited_turn = turn
                if location.first_visited_turn is None:
                    location.first_visited_turn = turn
                self.world_db.update_location(location)

                # 4. 返回细化结果
                return {
                    "narrative_text": refine_result.get("narrative_text", ""),
                    "affordances": refine_result.get("affordances", [])
                }
            else:
                # 已细化过，只重新提取可供性
                affordance_result = await self.scene_refinement.extract_affordances({
                    "location_id": location_id,
                    "character_state": character_state
                })

                return {
                    "narrative_text": "",  # 已访问过，不重复描述
                    "affordances": affordance_result.get("affordances", [])
                }

        except Exception as e:
            print(f"⚠️  进入地点时出错: {e}")
            return {"narrative_text": "", "affordances": []}

    def _get_world_style(self, location) -> Dict:
        """获取世界风格圣经"""
        if not self.world_db:
            return {}

        try:
            region = self.world_db.get_region(location.region_id)
            world = self.world_db.get_world(region.world_id)
            return world.style_bible.dict() if world.style_bible else {}
        except Exception:
            return {}

    async def process_turn(self, request: GameTurnRequest) -> GameTurnResponse:
        """处理游戏回合（非流式）"""
        state = request.currentState
        tools = GameTools(state)

        # 构建提示词
        system_prompt = self._build_system_prompt(state)
        context_prompt = self._build_context_prompt(state)

        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{context_prompt}\n\n玩家行动：{request.playerInput}"}
        ]

        # 调用LLM（带工具）
        try:
            # 导入LLMMessage
            from llm.base import LLMMessage

            # 合并所有消息到一个prompt
            full_prompt = "\n\n".join([msg["content"] for msg in messages if msg["role"] != "system"])
            system_msg = next((msg["content"] for msg in messages if msg["role"] == "system"), None)

            # 使用generate_structured来获取JSON格式输出
            response_schema = {
                "type": "object",
                "properties": {
                    "narration": {"type": "string", "description": "旁白文本"},
                    "tool_calls": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "arguments": {"type": "object"}
                            }
                        }
                    },
                    "hints": {"type": "array", "items": {"type": "string"}},
                    "suggestions": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["narration"]
            }

            # 构建包含工具定义的prompt
            tools_info = "\n\n".join([
                f"工具: {tool['name']}\n描述: {tool['description']}\n参数: {json.dumps(tool['input_schema'], ensure_ascii=False)}"
                for tool in GameTools.get_tool_definitions()
            ])

            enhanced_prompt = f"""{full_prompt}

可用工具:
{tools_info}

请返回JSON格式,包含narration(旁白)、tool_calls(工具调用列表)、hints(提示)、suggestions(建议)。
"""

            # 构建消息列表
            llm_messages = []
            if system_msg:
                llm_messages.append(LLMMessage(role="system", content=system_msg))
            llm_messages.append(LLMMessage(role="user", content=enhanced_prompt))

            # 使用新的后端抽象层
            response = await self.llm_backend.generate_structured(
                messages=llm_messages,
                response_schema=response_schema,
                temperature=0.7,
                max_tokens=1000
            )

            # 解析响应（response已经是解析好的JSON dict）
            narration = response.get("narration", "")
            tool_calls = response.get("tool_calls", [])
            hints = response.get("hints", [])
            suggestions = response.get("suggestions", [])

            # 执行工具调用
            executed_actions = []
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                arguments = tool_call.get("arguments", {})

                if hasattr(tools, tool_name):
                    func = getattr(tools, tool_name)
                    result = func(**arguments)

                    executed_actions.append({
                        "type": tool_name,
                        "arguments": arguments,
                        "result": result
                    })

            # 增加回合数
            state.world.time += 1

            # 记录日志
            tools.add_log("player", request.playerInput)
            tools.add_log("system", narration[:100] + "..." if len(narration) > 100 else narration)

            # ========== 任务系统更新 ==========
            quest_events = self.quest_engine.update_quests(
                state,
                tools,
                last_player_input=request.playerInput
            )

            # 将任务事件作为单独的区块展示
            if quest_events:
                quest_narration = "\n\n" + "=" * 40 + "\n"
                quest_narration += "📋 任务更新:\n"
                quest_narration += "\n".join(f"  • {event}" for event in quest_events)
                quest_narration += "\n" + "=" * 40
                narration += quest_narration

            # 获取任务提示
            quest_hints = self.quest_engine.get_active_quest_hints(state)
            if quest_hints:
                hints.extend(quest_hints[:2])  # 最多添加2个任务提示

            # ========== 世界系统集成 ==========
            # 检测位置变化，触发场景细化
            old_location = state.player.location  # 记录原位置（从执行前的状态）
            new_location = state.player.location  # 当前位置（可能被工具调用改变）

            # 检查是否有set_location工具调用
            location_changed = False
            for action in executed_actions:
                if action.get("type") == "set_location":
                    new_location = action["arguments"].get("location_id")
                    location_changed = True
                    break

            # 如果进入新地点，触发细化
            if location_changed and new_location != old_location and self.scene_refinement:
                try:
                    # 构建角色状态
                    character_state = {
                        "attributes": {attr: getattr(state.player, attr, 0) for attr in ["hp", "stamina", "money"]},
                        "inventory": [item.id for item in state.player.inventory]
                    }

                    # 调用进入地点逻辑
                    enter_result = await self._enter_location(
                        location_id=new_location,
                        turn=state.world.time,
                        character_state=character_state
                    )

                    # 如果有细化文本，追加到叙事中
                    if enter_result.get("narrative_text"):
                        narration += "\n\n" + "=" * 40 + "\n"
                        narration += "🗺️  场景描述:\n"
                        narration += enter_result["narrative_text"]
                        narration += "\n" + "=" * 40

                    # 如果有可供性chips，添加到建议中
                    if enter_result.get("affordances"):
                        for aff in enter_result["affordances"][:5]:  # 最多5个
                            chip = f"{aff.get('verb', '')}{aff.get('object', '')}"
                            if aff.get('risk'):
                                chip += " ⚠️"
                            suggestions.append(chip)

                except Exception as e:
                    print(f"⚠️  世界系统集成出错: {e}")

            return GameTurnResponse(
                narration=narration,
                actions=executed_actions,
                hints=hints,
                suggestions=suggestions,
                metadata={
                    "turn": state.world.time,
                    "toolCallsCount": len(tool_calls),
                    "activeQuests": len([q for q in state.quests if q.status == "active"]),
                    "questEvents": quest_events  # 添加任务事件到元数据
                }
            )

        except Exception as e:
            # 错误处理：返回安全的失败响应
            return GameTurnResponse(
                narration=f"[系统错误] 无法处理你的行动。请重试。(错误: {str(e)})",
                actions=[],
                hints=["尝试换一种说法"],
                suggestions=["查看背包", "查看任务", "环顾四周"]
            )

    async def process_turn_stream(
        self,
        request: GameTurnRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """处理游戏回合（流式） - 简化版本"""
        try:
            # 使用非流式处理，然后逐句发送
            response = await self.process_turn(request)

            # 将旁白按句子分割
            sentences = response.narration.split("。")
            for sentence in sentences:
                if sentence.strip():
                    yield {
                        "type": "text",
                        "content": sentence + "。"
                    }

            # 发送actions
            for action in response.actions:
                yield {
                    "type": "action",
                    "action": action
                }

            # 发送完成信号
            yield {
                "type": "done",
                "metadata": {
                    "hints": response.hints,
                    "suggestions": response.suggestions,
                    "turn": request.currentState.world.time
                }
            }

        except Exception as e:
            yield {
                "type": "error",
                "error": str(e)
            }

    def init_game(self, story_id: Optional[str] = None) -> GameState:
        """初始化游戏状态"""
        # 创建初始地图
        game_map = GameMap(
            nodes=[
                {
                    "id": "start",
                    "name": "起点",
                    "shortDesc": "一片空旷的广场",
                    "discovered": True,
                    "locked": False
                },
                {
                    "id": "forest",
                    "name": "迷雾森林",
                    "shortDesc": "笼罩在迷雾中的神秘森林",
                    "discovered": False,
                    "locked": False
                },
                {
                    "id": "cave",
                    "name": "古老洞穴",
                    "shortDesc": "散发着诡异气息的洞穴入口",
                    "discovered": False,
                    "locked": True,
                    "keyRequired": "cave_key"
                }
            ],
            edges=[
                {"from": "start", "to": "forest", "bidirectional": True},
                {"from": "forest", "to": "cave", "bidirectional": True}
            ],
            currentNodeId="start"
        )

        # 创建初始玩家
        player = PlayerState(
            hp=100,
            maxHp=100,
            stamina=100,
            maxStamina=100,
            traits=["勇敢", "好奇"],
            inventory=[],
            location="start",
            money=50
        )

        # 创建初始世界
        world = WorldState(
            time=0,
            flags={},
            discoveredLocations=["start"],
            variables={}
        )

        # 创建初始状态
        state = GameState(
            version="1.0.0",
            player=player,
            world=world,
            quests=[],
            map=game_map,
            log=[]
        )

        return state
