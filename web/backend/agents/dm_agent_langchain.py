"""
DM Agent - 游戏主持人 Agent (LangChain 1.0 实现)
从 Claude Agent SDK 迁移到 LangChain

支持两种模式：
1. 默认模式：使用 game_state.log 手动管理对话历史（推荐）
2. Checkpoint 模式：使用 LangGraph Checkpoint 自动管理（可选）
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

from .game_tools_langchain import ALL_GAME_TOOLS, set_current_session_id

# 可选：导入 Checkpoint（如果启用）
try:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    CHECKPOINT_AVAILABLE = True
except ImportError:
    CHECKPOINT_AVAILABLE = False
    logger.warning("⚠️  LangGraph Checkpoint 未安装，使用默认模式")


class DMAgentLangChain:
    """游戏主持人 Agent (LangChain 实现)"""

    def __init__(
        self,
        model_name: str = None,
        use_checkpoint: bool = False,
        checkpoint_db: str = "data/checkpoints/dm.db",
    ):
        """
        初始化 DM Agent

        Args:
            model_name: 模型名称，默认从环境变量 DEFAULT_MODEL 读取
            use_checkpoint: 是否使用 LangGraph Checkpoint（默认 False）
            checkpoint_db: Checkpoint 数据库路径（仅在 use_checkpoint=True 时有效）
        """
        # 模型名称映射
        self.model_map = {
            "deepseek": "deepseek/deepseek-v3.1-terminus",
            "claude-sonnet": "anthropic/claude-3.5-sonnet",
            "claude-haiku": "anthropic/claude-3-haiku",
            "gpt-4": "openai/gpt-4-turbo",
            "qwen": "qwen/qwen-2.5-72b-instruct",
            "kimi": "deepseek/deepseek-v3.1-terminus",
        }

        # 获取模型名称
        if model_name is None:
            model_name = os.getenv("DEFAULT_MODEL")
            if not model_name:
                logger.warning(
                    "⚠️  DEFAULT_MODEL 环境变量未设置，使用 fallback: deepseek/deepseek-v3.1-terminus"
                )
                model_name = "deepseek/deepseek-v3.1-terminus"

        # 映射简写到完整名称
        full_model_name = self.model_map.get(model_name, model_name)

        # 初始化 OpenRouter 模型
        self.model = ChatOpenAI(
            model=full_model_name,
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=0.7,
            max_tokens=4096,
            streaming=True,
        )

        # 游戏工具
        self.tools = ALL_GAME_TOOLS

        # Checkpoint 配置
        self.use_checkpoint = use_checkpoint and CHECKPOINT_AVAILABLE
        self.checkpoint_db = checkpoint_db
        self.checkpointer = None

        if self.use_checkpoint:
            if not CHECKPOINT_AVAILABLE:
                logger.warning("⚠️  Checkpoint 模式已请求，但 langgraph-checkpoint-sqlite 未安装")
                logger.warning("   将使用默认模式（game_state.log）")
                self.use_checkpoint = False
            else:
                Path(checkpoint_db).parent.mkdir(parents=True, exist_ok=True)
                # 🔥 创建 SqliteSaver（同步版本，适用于长期运行的服务）
                try:
                    import sqlite3

                    from langgraph.checkpoint.sqlite import SqliteSaver

                    conn = sqlite3.connect(checkpoint_db, check_same_thread=False)
                    self.checkpointer = SqliteSaver(conn)
                    logger.info(f"✅ Checkpoint 模式已启用: {checkpoint_db}")
                except Exception as e:
                    logger.error(f"❌ 初始化 Checkpoint 失败: {e}")
                    self.use_checkpoint = False

        logger.info("=" * 80)
        logger.info(f"🎮 DM Agent 初始化完成")
        logger.info(f"📦 使用模型: {full_model_name}")
        logger.info(f"🔧 加载工具数量: {len(self.tools)}")
        logger.debug(f"🔧 可用工具列表: {[tool.name for tool in self.tools]}")
        if self.use_checkpoint:
            logger.info(f"💾 记忆模式: LangGraph Checkpoint")
        else:
            logger.info(f"💾 记忆模式: game_state.log (默认)")
        logger.info("=" * 80)

    def _build_system_prompt(self, game_state: Dict[str, Any]) -> str:
        """构建系统提示词"""
        return f"""你是一个单人跑团游戏的游戏主持人（DM）。

🎯 叙事连贯性规则（最高优先级）:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【严格遵守】你会收到完整的对话历史，包括之前所有的玩家行动和你的DM回复。

✅ 正确做法:
1. 仔细阅读最近3-5条对话历史
2. 识别当前场景的最新状态（如：松鼠已经接住硬币并塞进颊囊）
3. 基于最新状态继续场景发展，推进剧情
4. 如果玩家说"跟上去"，意味着跟随你刚刚提到的角色/对象
5. 如果玩家说"继续"、"然后呢"，继续讲述当前场景

❌ 禁止行为:
- 不要重复描述已经发生过的动作！
- 不要重新描述已经交互过的物品/NPC！
- 不要突然跳转场景或倒回时间线！
- 不要忽略玩家的最新行动！

【示例】错误 vs 正确:
错误: 玩家说"跟上去" → DM重复描述"金币从你手中滑落..." ❌
正确: 玩家说"跟上去" → DM描述"你追随着松鼠的脚步，穿过树林..." ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
   - remove_item: 移除物品（玩家给予/消耗物品时）
   - update_hp: 修改HP
   - roll_check: 进行技能检定
   - set_location: 移动到新位置
   - create_quest: 创建新任务
   - create_npc: 创建NPC
5. 提供2-3个有趣的行动建议

工具调用规则:
- 当玩家给予物品时，调用 remove_item（如：给NPC一个硬币）
- 当玩家获得物品时，调用 add_item
- 战斗时要调用 roll_check 和 update_hp
- 移动到新地点时要调用 set_location
- 遇到新NPC时可以调用 create_npc

叙述风格:
- 使用第二人称("你")与玩家互动
- 描述要生动形象，调动五感
- 适当留白，让玩家有想象空间
- 节奏要张弛有度
"""

    def _save_to_log(self, game_state: Dict[str, Any], player_action: str, dm_response: str):
        """保存对话到游戏日志

        Args:
            game_state: 游戏状态
            player_action: 玩家行动
            dm_response: DM回复
        """
        import time

        # 确保 log 列表存在
        if "log" not in game_state:
            game_state["log"] = []

        # 添加玩家行动
        game_state["log"].append(
            {"actor": "player", "text": player_action, "timestamp": int(time.time())}
        )

        # 添加DM回复（如果有）
        if dm_response and dm_response.strip():
            game_state["log"].append(
                {"actor": "dm", "text": dm_response, "timestamp": int(time.time())}
            )

        logger.debug(f"📝 已保存到日志: 玩家输入 + DM回复 (共 {len(game_state['log'])} 条)")

    def _build_message_history(
        self, game_state: Dict[str, Any], current_player_action: str
    ) -> List[Dict[str, str]]:
        """从游戏日志构建完整的消息历史

        Args:
            game_state: 当前游戏状态
            current_player_action: 当前玩家行动

        Returns:
            消息历史列表 [{"role": "user"|"assistant", "content": str}]
        """
        messages = []

        # 🔥 修复：从 game_state.log 读取历史对话（不是 logs）
        # log 格式: List[GameLogEntry] = [{"actor": str, "text": str, "timestamp": int}]
        log_entries = game_state.get("log", [])

        # 只取最近10条日志（避免上下文过长）
        recent_logs = log_entries[-10:] if len(log_entries) > 10 else log_entries

        for log_entry in recent_logs:
            # 兼容两种格式：dict 和 object
            if isinstance(log_entry, dict):
                actor = log_entry.get("actor", "unknown")
                text = log_entry.get("text", "")
            else:
                # 如果是 GameLogEntry 对象
                actor = getattr(log_entry, "actor", "unknown")
                text = getattr(log_entry, "text", "")

            if actor == "player":
                messages.append({"role": "user", "content": f"玩家行动: {text}"})
            elif actor == "system" or actor == "dm":
                messages.append({"role": "assistant", "content": text})

        # 添加当前玩家行动
        messages.append(
            {
                "role": "user",
                "content": f"玩家行动: {current_player_action}\n\n请作为DM处理这个行动，使用工具更新游戏状态，并生成精彩的场景描述。",
            }
        )

        return messages

    async def process_turn(
        self, session_id: str, player_action: str, game_state: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """处理游戏回合 (流式)

        Args:
            session_id: 会话ID（用于区分不同玩家）
            player_action: 玩家行动
            game_state: 当前游戏状态

        Yields:
            消息事件（narration/tool_call/tool_result/complete）
        """
        logger.info("=" * 80)
        logger.info(f"🎲 开始处理游戏回合 (流式)")
        logger.info(f"🆔 会话ID: {session_id}")
        logger.info(f"📝 玩家行动: {player_action}")
        logger.debug(f"🗺️  当前位置: {game_state.get('player', {}).get('location', '未知')}")
        logger.debug(f"🎯 回合数: {game_state.get('turn_number', 0)}")

        # 设置当前会话
        set_current_session_id(session_id)

        # 构建系统提示词
        system_prompt = self._build_system_prompt(game_state)
        logger.debug("📋 SYSTEM PROMPT:")
        logger.debug(system_prompt[:300] + "..." if len(system_prompt) > 300 else system_prompt)

        # 创建 agent
        logger.info("🤖 创建 LangChain Agent...")

        # 🔥 Checkpoint 模式：使用 checkpointer
        if self.use_checkpoint and self.checkpointer:
            logger.info(f"💾 使用 Checkpoint 模式 (thread_id: {session_id})")

            # 使用 langgraph 的 create_react_agent，支持 checkpointer
            from langgraph.prebuilt import create_react_agent

            agent = create_react_agent(
                model=self.model,
                tools=self.tools,
                checkpointer=self.checkpointer,  # 👈 启用自动记忆
            )

            # Checkpoint 模式：只传入当前玩家行动（历史会自动加载）
            message_history = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"玩家行动: {player_action}\n\n请作为DM处理这个行动，使用工具更新游戏状态，并生成精彩的场景描述。",
                },
            ]
            config = {
                "configurable": {"thread_id": session_id}
            }  # 👈 使用 session_id 作为 thread_id

        else:
            # 默认模式：手动构建消息历史
            logger.info("📝 使用默认模式 (game_state.log)")
            agent = create_agent(model=self.model, tools=self.tools, system_prompt=system_prompt)

            # 🔥 构建完整的消息历史（从 game_state.log 读取）
            message_history = self._build_message_history(game_state, player_action)
            logger.info(f"📚 消息历史长度: {len(message_history)} 条")
            logger.debug("📨 MESSAGE HISTORY:")
            for i, msg in enumerate(message_history[-5:]):  # 只显示最后5条
                logger.debug(f"   [{i}] {msg['role']}: {msg['content'][:80]}...")

            config = None

        try:
            logger.info("🚀 开始流式处理...")

            # 🔥 收集完整的叙事文本，用于保存到日志
            full_narration = []

            # 流式调用
            if config:
                # Checkpoint 模式：使用 astream 而非 astream_events
                # 🔥 增强版：手动从消息中提取工具调用和思考过程
                async for event in agent.astream({"messages": message_history}, config=config):
                    # 处理 langgraph 的 event 格式
                    if "agent" in event:
                        agent_event = event["agent"]
                        if "messages" in agent_event:
                            for msg in agent_event["messages"]:
                                # 🔥 检测工具调用 (AIMessage 中的 tool_calls)
                                if hasattr(msg, "tool_calls") and msg.tool_calls:
                                    for tool_call in msg.tool_calls:
                                        tool_name = tool_call.get("name")
                                        tool_args = tool_call.get("args", {})
                                        logger.info(f"🔧 检测到工具调用: {tool_name}")
                                        yield {
                                            "type": "tool_call",
                                            "tool": tool_name,
                                            "input": tool_args
                                        }

                                # 🔥 检测工具返回结果 (ToolMessage)
                                if hasattr(msg, "type") and msg.type == "tool":
                                    tool_name = getattr(msg, "name", "unknown")
                                    logger.info(f"✅ 检测到工具返回: {tool_name}")
                                    yield {
                                        "type": "tool_result",
                                        "tool": tool_name,
                                        "output": msg.content
                                    }

                                # 🔥 处理文本内容（叙事 + 思考过程检测）
                                if hasattr(msg, "content") and msg.content:
                                    content = msg.content

                                    # 检测思考过程标记
                                    if "<thinking>" in content or "思考：" in content:
                                        yield {"type": "thinking_start", "content": ""}
                                    elif "</thinking>" in content:
                                        yield {"type": "thinking_end", "content": ""}
                                    elif any(marker in content for marker in ["<think>", "推理：", "分析："]):
                                        # 思考步骤
                                        yield {"type": "thinking_step", "content": content}
                                    else:
                                        # 正常叙事内容
                                        full_narration.append(content)
                                        yield {"type": "narration", "content": content}
            else:
                # 默认模式：使用 astream_events
                async for event in agent.astream_events(
                    {"messages": message_history}, version="v2"
                ):
                    event_type = event.get("event")

                    # 文本流
                    if event_type == "on_chat_model_stream":
                        chunk = event.get("data", {}).get("chunk", {})
                        if hasattr(chunk, "content") and chunk.content:
                            logger.debug(f"💬 叙事片段: {chunk.content[:50]}...")
                            full_narration.append(chunk.content)  # 🔥 收集叙事文本

                            # 🔥 检测 Kimi K2 思考过程标记 (thinking_start/thinking_end)
                            content = chunk.content
                            if "<thinking>" in content or "思考：" in content:
                                yield {"type": "thinking_start", "content": ""}
                            elif "</thinking>" in content:
                                yield {"type": "thinking_end", "content": ""}
                            elif any(
                                marker in content for marker in ["<think>", "推理：", "分析："]
                            ):
                                # Kimi K2 思考步骤
                                yield {"type": "thinking_step", "content": content}
                            else:
                                # 正常叙事内容
                                yield {"type": "narration", "content": chunk.content}

                    # 工具调用开始
                    elif event_type == "on_tool_start":
                        tool_name = event.get("name")
                        tool_input = event.get("data", {}).get("input", {})
                        logger.info(f"🔧 工具调用开始: {tool_name}")
                        logger.debug(f"   输入参数: {json.dumps(tool_input, ensure_ascii=False)}")
                        yield {"type": "tool_call", "tool": tool_name, "input": tool_input}

                    # 工具调用结束
                    elif event_type == "on_tool_end":
                        tool_name = event.get("name")
                        tool_output = event.get("data", {}).get("output")
                        logger.info(f"✅ 工具调用完成: {tool_name}")
                        # 🔥 安全地记录输出（避免序列化错误）
                        try:
                            output_str = json.dumps(tool_output, ensure_ascii=False)[:200]
                            logger.debug(f"   输出结果: {output_str}...")
                        except (TypeError, ValueError):
                            logger.debug(f"   输出结果: {str(tool_output)[:200]}...")
                        yield {"type": "tool_result", "tool": tool_name, "output": tool_output}

            # 🔥 保存玩家输入和DM回复到游戏日志
            self._save_to_log(game_state, player_action, "".join(full_narration))

        except Exception as e:
            logger.error(f"❌ 处理回合时出错: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            yield {"type": "error", "message": f"处理回合时出错: {str(e)}"}

        # 更新回合数
        game_state["turn_number"] = game_state.get("turn_number", 0) + 1
        logger.info(f"🎯 回合完成，当前回合数: {game_state['turn_number']}")
        logger.info("=" * 80)

        yield {"type": "complete", "turn": game_state["turn_number"]}

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
        logger.info("=" * 80)
        logger.info(f"🎲 开始处理游戏回合 (非流式)")
        logger.info(f"🆔 会话ID: {session_id}")
        logger.info(f"📝 玩家行动: {player_action}")

        # 设置当前会话
        set_current_session_id(session_id)

        # 构建系统提示词
        system_prompt = self._build_system_prompt(game_state)
        logger.debug("📋 SYSTEM PROMPT (前300字):")
        logger.debug(system_prompt[:300] + "...")

        # 创建 agent
        logger.info("🤖 创建 LangChain Agent...")
        agent = create_agent(model=self.model, tools=self.tools, system_prompt=system_prompt)

        # 🔥 构建完整的消息历史（从 game_state.logs 读取）
        message_history = self._build_message_history(game_state, player_action)
        logger.info(f"📚 消息历史长度: {len(message_history)} 条")
        logger.debug("📨 MESSAGE HISTORY:")
        for i, msg in enumerate(message_history[-5:]):  # 只显示最后5条
            logger.debug(f"   [{i}] {msg['role']}: {msg['content'][:80]}...")

        # 收集所有消息
        narration_parts = []
        tool_calls = []

        try:
            logger.info("🚀 调用 Agent...")

            # 调用 agent (非流式) - 传递完整的消息历史
            result = await agent.ainvoke({"messages": message_history})

            logger.debug(f"📦 Agent 返回结果: {type(result)}")

            # 解析结果
            messages = result.get("messages", [])
            logger.info(f"📨 收到 {len(messages)} 条消息")

            for i, message in enumerate(messages):
                logger.debug(f"   消息 {i+1}: {type(message).__name__}")

                # 提取文本内容
                if hasattr(message, "content") and message.content:
                    narration_parts.append(message.content)
                    logger.debug(f"   💬 叙事内容: {message.content[:100]}...")

                # 提取工具调用
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.get("name")
                        tool_args = tool_call.get("args", {})
                        logger.info(f"   🔧 工具调用: {tool_name}")
                        logger.debug(f"      参数: {json.dumps(tool_args, ensure_ascii=False)}")
                        tool_calls.append({"tool": tool_name, "input": tool_args})

            logger.info(
                f"✅ 处理完成: 叙事 {len(narration_parts)} 段, 工具调用 {len(tool_calls)} 次"
            )

        except Exception as e:
            logger.error(f"❌ 处理回合时出错: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            return {
                "narration": f"处理回合时出错: {str(e)}",
                "tool_calls": [],
                "updated_state": game_state,
                "turn": game_state.get("turn_number", 0),
                "error": str(e),
            }

        # 🔥 保存玩家输入和DM回复到游戏日志
        full_narration = "\n\n".join(narration_parts)
        self._save_to_log(game_state, player_action, full_narration)

        # 更新回合数
        game_state["turn_number"] = game_state.get("turn_number", 0) + 1
        logger.info(f"🎯 回合完成，当前回合数: {game_state['turn_number']}")
        logger.info("=" * 80)

        return {
            "narration": full_narration,
            "tool_calls": tool_calls,
            "updated_state": game_state,
            "turn": game_state["turn_number"],
        }

    def get_model_name(self) -> str:
        """获取当前使用的模型名称"""
        return self.model.model_name


# ============= 向后兼容别名 =============

DMAgent = DMAgentLangChain
