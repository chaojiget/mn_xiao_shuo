"""
游戏引擎 - 处理游戏回合，集成LLM与工具调用
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel
from utils.logger import get_logger
logger = get_logger(__name__)

from .game_tools import GameMap, GameState, GameTools, PlayerState, RollCheckParams, WorldState
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

    def __init__(
        self, llm_backend, quest_data_path: Optional[str] = None, db_path: Optional[str] = None
    ):
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
                logger.info("✅ 世界系统已启用")
            except Exception as e:
                logger.error(f"⚠️  世界系统初始化失败: {e}")
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
1. 根据玩家输入，生成沉浸式的旁白描述（200-400字，详细生动）
2. **必须**通过工具调用更新游戏状态（生命值、物品、位置等）
3. **严格保持叙事连贯性** - 继续上一回合的场景，不要突然跳转
4. 提供有趣的挑战、细节描述和感官体验

**输出格式要求**：
你必须返回JSON格式，包含以下字段：
{{
  "narration": "沉浸式的旁白文本（详细描述玩家的感受、环境细节、NPC反应等）",
  "tool_calls": [
    {{"name": "工具名", "arguments": {{...}}}}
  ],
  "hints": ["可选的提示信息"],
  "suggestions": ["玩家可能的下一步行动建议（3-5个）"]
}}

**❗ 关键规则（必须遵守）**：
1. **物品操作规则**：
   - 玩家扔掉/使用/丢弃物品 → 必须调用 `remove_item` 工具
   - 玩家获得物品 → 必须调用 `add_item` 工具
   - 玩家移动位置 → 必须调用 `set_location` 工具
   - 玩家受伤/治疗 → 必须调用 `update_hp` 工具

2. **叙事连贯性规则**：
   - 阅读"最近发生"中的事件，**必须延续上一回合的场景**
   - 如果玩家在通风管道，继续在通风管道
   - 如果玩家在对话，继续对话
   - 不要突然跳转到其他场景
   - 如果玩家提问（如"回应啥？"），解释上一回合提到的内容

3. **描述详细度**：
   - 每个场景至少200字
   - 包含：视觉、听觉、触觉、气味等感官细节
   - 描述NPC的表情、语气、动作
   - 描述环境的氛围、光线、温度

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

        # 获取背包详细信息（包含完整物品列表）
        inventory_info = "\n".join(
            [
                f"  - {item.name} x{item.quantity} ({item.description if hasattr(item, 'description') and item.description else item.type})"
                for item in state.player.inventory[:10]
            ]
        )

        # 获取近期日志（更多回合，更完整的上下文）
        recent_logs = state.log[-8:] if state.log else []  # 从5条增加到8条
        logs_info = "\n".join(
            [
                f"  [{entry.actor}] {entry.text[:100]}..."  # 从50字增加到100字
                for entry in recent_logs
            ]
        )

        # 🔥 关键改进：将"最近发生"放在最前面，强调连贯性
        return f"""
**❗ 重要：请阅读"最近发生"，延续上一回合的场景！**

**最近发生的事件**（必须延续这些场景）：
{logs_info or "  这是游戏开始"}

---

**当前位置标记**（仅供参考，实际场景以"最近发生"为准）：
{location_info}

**活跃任务**：
{quests_info or "  无"}

**背包物品**（扔掉/使用时必须调用remove_item工具）：
{inventory_info or "  空"}
"""

    async def _enter_location(
        self, location_id: str, turn: int, character_state: Dict
    ) -> Dict[str, Any]:
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
            return {"narrative_text": "", "affordances": []}

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
                        "passes": ["structure", "sensory", "affordance", "cinematic"],
                    },
                    world_style=self._get_world_style(location),
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
                    "affordances": refine_result.get("affordances", []),
                }
            else:
                # 已细化过，只重新提取可供性
                affordance_result = await self.scene_refinement.extract_affordances(
                    {"location_id": location_id, "character_state": character_state}
                )

                return {
                    "narrative_text": "",  # 已访问过，不重复描述
                    "affordances": affordance_result.get("affordances", []),
                }

        except Exception as e:
            logger.warning(f"⚠️  进入地点时出错: {e}")
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
        logger.info("=" * 80)
        logger.info(f"🎮 开始处理游戏回合")
        logger.info(f"📝 玩家输入: {request.playerInput}")

        state = request.currentState
        tools = GameTools(state)

        # 记录当前游戏状态
        logger.debug(f"🗺️  当前位置: {state.player.location}")
        logger.debug(
            f"❤️  玩家状态: HP={state.player.hp}/{state.player.maxHp}, 金币={state.player.money}"
        )
        logger.debug(f"🎒 背包物品: {len(state.player.inventory)} 件")
        logger.debug(f"⏱️  当前回合: {state.world.time}")

        # 构建提示词
        system_prompt = self._build_system_prompt(state)
        context_prompt = self._build_context_prompt(state)

        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{context_prompt}\n\n玩家行动：{request.playerInput}"},
        ]

        # 调用LLM（带工具）
        try:
            # 合并所有消息到一个prompt
            full_prompt = "\n\n".join(
                [msg["content"] for msg in messages if msg["role"] != "system"]
            )
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
                                "arguments": {"type": "object"},
                            },
                        },
                    },
                    "hints": {"type": "array", "items": {"type": "string"}},
                    "suggestions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["narration"],
            }

            # 构建包含工具定义的prompt
            tools_info = "\n\n".join(
                [
                    f"工具: {tool['name']}\n描述: {tool['description']}\n参数: {json.dumps(tool['input_schema'], ensure_ascii=False)}"
                    for tool in GameTools.get_tool_definitions()
                ]
            )

            enhanced_prompt = f"""{full_prompt}

可用工具:
{tools_info}

请返回JSON格式,包含narration(旁白)、tool_calls(工具调用列表)、hints(提示)、suggestions(建议)。
"""

            # ===== 详细日志：发送给 LLM 的内容 =====
            logger.info("🤖 准备调用 LLM")
            logger.debug("=" * 60)
            logger.debug("📋 SYSTEM PROMPT:")
            logger.debug(system_msg[:500] + "..." if len(system_msg) > 500 else system_msg)
            logger.debug("-" * 60)
            logger.debug("📋 USER PROMPT (前500字符):")
            logger.debug(
                enhanced_prompt[:500] + "..." if len(enhanced_prompt) > 500 else enhanced_prompt
            )
            logger.debug("-" * 60)
            logger.debug("📊 RESPONSE SCHEMA:")
            logger.debug(json.dumps(response_schema, indent=2, ensure_ascii=False))
            logger.debug("=" * 60)

            # 使用新的后端抽象层 (LangChain 需要 prompt + schema 参数)
            response = await self.llm_backend.generate_structured(
                prompt=enhanced_prompt,
                schema=response_schema,
                system=system_msg,
                temperature=0.7,
                max_tokens=1000,
            )

            # ===== 详细日志：LLM 的响应 =====
            logger.info("✅ LLM 响应成功")
            logger.debug("=" * 60)
            logger.debug("📨 LLM RESPONSE (完整 JSON):")
            logger.debug(json.dumps(response, indent=2, ensure_ascii=False))
            logger.debug("=" * 60)

            # 解析响应（response已经是解析好的JSON dict）
            narration = response.get("narration", "")
            tool_calls = response.get("tool_calls", [])
            hints = response.get("hints", [])
            suggestions = response.get("suggestions", [])

            logger.info(f"📖 旁白长度: {len(narration)} 字符")
            logger.info(f"🛠️  工具调用数量: {len(tool_calls)}")
            logger.info(f"💡 提示数量: {len(hints)}")
            logger.info(f"🎯 建议数量: {len(suggestions)}")

            # 执行工具调用
            executed_actions = []
            for i, tool_call in enumerate(tool_calls, 1):
                tool_name = tool_call.get("name")
                arguments = tool_call.get("arguments", {})

                logger.debug(f"🔧 工具调用 #{i}: {tool_name}")
                logger.debug(f"   参数: {json.dumps(arguments, ensure_ascii=False)}")

                if hasattr(tools, tool_name):
                    func = getattr(tools, tool_name)
                    result = func(**arguments)

                    logger.debug(f"   ✅ 结果: {result}")

                    executed_actions.append(
                        {"type": tool_name, "arguments": arguments, "result": result}
                    )
                else:
                    logger.warning(f"   ⚠️  工具不存在: {tool_name}")

            # 增加回合数
            state.world.time += 1

            # 记录日志
            tools.add_log("player", request.playerInput)
            tools.add_log("system", narration)  # 🔥 修复：保存完整叙事，不截断

            # ========== 任务系统更新 ==========
            quest_events = self.quest_engine.update_quests(
                state, tools, last_player_input=request.playerInput
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
                        "attributes": {
                            attr: getattr(state.player, attr, 0)
                            for attr in ["hp", "stamina", "money"]
                        },
                        "inventory": [item.id for item in state.player.inventory],
                    }

                    # 调用进入地点逻辑
                    enter_result = await self._enter_location(
                        location_id=new_location,
                        turn=state.world.time,
                        character_state=character_state,
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
                            if aff.get("risk"):
                                chip += " ⚠️"
                            suggestions.append(chip)

                except Exception as e:
                    logger.error(f"⚠️  世界系统集成出错: {e}")
                    logger.warning(f"⚠️  世界系统集成出错: {e}")

            # 最终响应日志
            final_response = GameTurnResponse(
                narration=narration,
                actions=executed_actions,
                hints=hints,
                suggestions=suggestions,
                metadata={
                    "turn": state.world.time,
                    "toolCallsCount": len(tool_calls),
                    "activeQuests": len([q for q in state.quests if q.status == "active"]),
                    "questEvents": quest_events,  # 添加任务事件到元数据
                },
            )

            logger.info(f"🎬 回合完成 (第 {state.world.time} 回合)")
            logger.info(
                f"📜 旁白前100字: {narration[:100]}..."
                if len(narration) > 100
                else f"📜 旁白: {narration}"
            )
            logger.info("=" * 80)

            return final_response

        except Exception as e:
            # 错误处理：返回安全的失败响应
            logger.error(f"❌ 处理回合时发生错误: {str(e)}", exc_info=True)
            logger.error("=" * 80)
            return GameTurnResponse(
                narration=f"[系统错误] 无法处理你的行动。请重试。(错误: {str(e)})",
                actions=[],
                hints=["尝试换一种说法"],
                suggestions=["查看背包", "查看任务", "环顾四周"],
            )

    async def process_turn_stream(self, request: GameTurnRequest) -> AsyncIterator[Dict[str, Any]]:
        """处理游戏回合（流式） - 增强版本，支持工具调用可视化"""
        try:
            # 使用非流式处理，然后逐句发送
            response = await self.process_turn(request)

            # 🔥 先发送工具调用事件（如果有）
            if response.actions:
                for action in response.actions:
                    # 解析 action 字典，提取工具名称和参数
                    # action 格式: {"type": "tool_name", "arguments": {...}, "result": ...}
                    tool_name = action.get("type", "unknown_tool")
                    tool_args = action.get("arguments", {})

                    # 发送工具调用开始事件
                    yield {"type": "tool_call", "tool": tool_name, "input": tool_args}

                    # 发送工具调用结果事件
                    yield {
                        "type": "tool_result",
                        "tool": tool_name,
                        "output": action.get("result", "执行成功"),
                    }

            # 将旁白按句子分割，逐句流式发送
            sentences = response.narration.split("。")
            for sentence in sentences:
                if sentence.strip():
                    yield {"type": "text", "content": sentence + "。"}

            # 发送完成信号
            yield {
                "type": "done",
                "metadata": {
                    "hints": response.hints,
                    "suggestions": response.suggestions,
                    "turn": request.currentState.world.time,
                    "tool_calls_count": len(response.actions) if response.actions else 0,
                },
            }

        except Exception as e:
            yield {"type": "error", "error": str(e)}

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
                    "locked": False,
                },
                {
                    "id": "forest",
                    "name": "迷雾森林",
                    "shortDesc": "笼罩在迷雾中的神秘森林",
                    "discovered": False,
                    "locked": False,
                },
                {
                    "id": "cave",
                    "name": "古老洞穴",
                    "shortDesc": "散发着诡异气息的洞穴入口",
                    "discovered": False,
                    "locked": True,
                    "keyRequired": "cave_key",
                },
            ],
            edges=[
                {"from": "start", "to": "forest", "bidirectional": True},
                {"from": "forest", "to": "cave", "bidirectional": True},
            ],
            currentNodeId="start",
        )

        # 创建初始玩家
        from .game_tools import InventoryItem

        player = PlayerState(
            hp=100,
            maxHp=100,
            stamina=100,
            maxStamina=100,
            traits=["勇敢", "好奇"],
            inventory=[
                InventoryItem(
                    id="gold_coin",
                    name="金币",
                    description="闪闪发光的金币，可以用于交易或吸引注意力",
                    quantity=50,
                    type="misc",
                )
            ],
            location="start",
            money=0,  # 金币现在在背包中
        )

        # 创建初始世界
        world = WorldState(time=0, flags={}, discoveredLocations=["start"], variables={})

        # 🔥 生成唯一的 session_id
        import uuid

        session_id = f"game_{uuid.uuid4().hex[:16]}"

        # 创建初始状态
        state = GameState(
            version="1.0.0",
            session_id=session_id,  # 👈 设置 session_id
            player=player,
            world=world,
            quests=[],
            map=game_map,
            log=[],
        )

        return state
