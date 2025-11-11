"""
DM Graph Agent - 基于 LangGraph 的 DM 实现（最小可用版本）

目标：
- 使用 LangGraph 的 create_react_agent + SqliteSaver 实现持久化对话与可回溯
- 复用现有 LangChain 工具（agents/game_tools_langchain.py 中定义的 @tool）
- 提供与现有 DMActionResponse 兼容的同步接口（后续再扩展流式/中断）
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from services.world_indexer import create_world_indexer
from config.settings import settings

try:
    # 持久化检查点（线程隔离、可回溯）
    from langgraph.checkpoint.sqlite import SqliteSaver

    _CHECKPOINT_AVAILABLE = True
except Exception:
    _CHECKPOINT_AVAILABLE = False

from config.settings import settings
from utils.logger import get_logger

# 复用现有工具与状态上下文
from agents.game_tools_langchain import ALL_GAME_TOOLS, set_state
from game.game_tools import GameState


logger = get_logger(__name__)


class DMGraphAgent:
    """基于 LangGraph 的 DM Agent（非流式最小实现）"""

    def __init__(
        self,
        model_name: Optional[str] = None,
        checkpoint_db: Optional[str] = None,
    ) -> None:
        # 模型映射（与旧版保持一致简写）
        model_map = {
            "deepseek": "deepseek/deepseek-v3.1-terminus",
            "claude-sonnet": "anthropic/claude-3.5-sonnet",
            "claude-haiku": "anthropic/claude-3-haiku",
            "gpt-4": "openai/gpt-4-turbo",
            "qwen": "qwen/qwen-2.5-72b-instruct",
            "kimi": "deepseek/deepseek-v3.1-terminus",
        }

        # 解析模型名
        # 优先使用传入；否则使用统一 settings.default_model（settings 会从 .env / 环境变量读取）
        model_name = model_name or settings.default_model
        full_model = model_map.get(model_name, model_name)

        # 创建 LLM（走 OpenRouter）
        self.model = ChatOpenAI(
            model=full_model,
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            temperature=settings.llm_temperature,
            max_tokens=min(settings.llm_max_tokens, 4096),
            streaming=True,
        )

        # Checkpointer（可选）
        self.checkpointer = None
        if _CHECKPOINT_AVAILABLE:
            db_path = (
                Path(checkpoint_db)
                if checkpoint_db
                else settings.checkpoint_db_path
            )
            db_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                self.checkpointer = SqliteSaver.from_conn_string(str(db_path))
                logger.info(f"✅ LangGraph Checkpointer 启用: {db_path}")
            except Exception as e:
                logger.warning(f"⚠️  Checkpointer 初始化失败，将以无记忆模式运行: {e}")
                self.checkpointer = None
        else:
            logger.warning("⚠️  未安装 langgraph-checkpoint-sqlite，将以无记忆模式运行")

        # 构建 ReAct Agent（复用现有工具）
        self.tools = ALL_GAME_TOOLS
        self.agent = create_react_agent(
            model=self.model,
            tools=self.tools,
            checkpointer=self.checkpointer,
        )

        logger.info("=" * 60)
        logger.info("🎮 DMGraphAgent 初始化完成")
        logger.info(f"📦 模型: {full_model}")
        logger.info(f"🔧 工具数: {len(self.tools)}")
        logger.info("=" * 60)

    def _system_prompt(self, game_state: Dict[str, Any]) -> str:
        summary = (
            game_state.get("metadata", {}).get("log_summary")
            or game_state.get("world", {}).get("variables", {}).get("conversation_summary")
        )
        base = (
            "你是单人跑团的地下城主（DM）。保持叙事连贯，必要时调用工具更新状态。\n"
            "工具调用规则：\n"
            "- 玩家给予物品 → remove_item；获得物品 → add_item\n"
            "- 战斗 → roll_check + update_hp；移动 → set_location\n"
            "- 新NPC → create_npc；任务 → create_quest / update_quest_objective\n"
            "- 命名实体/背景设定 → 优先调用 search_world_kb(query) 检索世界百科后再叙述\n"
        )
        if summary:
            return (
                base
                + "\n\n【对话摘要（已压缩历史）】\n"
                + str(summary)[:2000]
            )
        return base

    def _get_world_id(self, game_state: Dict[str, Any]) -> Optional[str]:
        """从游戏状态中提取 worldId。"""
        md = game_state.get("metadata", {}) if isinstance(game_state, dict) else {}
        world_id = md.get("worldPackId") or md.get("world_id")
        if not world_id:
            world = game_state.get("world", {}) if isinstance(game_state, dict) else {}
            variables = world.get("variables", {}) if isinstance(world, dict) else {}
            world_id = variables.get("worldPackId") or variables.get("world_id")
        return world_id

    def _retrieve_snippets(self, player_action: str, game_state: Dict[str, Any], top_k: int = 5) -> str:
        """对世界百科进行检索，并返回可拼接到提示词的片段。"""
        try:
            world_id = self._get_world_id(game_state)
            if not world_id:
                return ""
            indexer = create_world_indexer(str(settings.database_path))
            results = indexer.search(world_id, player_action, None, top_k)
            if not results:
                return ""
            lines = ["【世界检索结果】（用于设定一致性）"]
            for r in results:
                kind = r.get("kind", "fact")
                ref = r.get("ref_id") or r.get("id") or "unknown"
                content = r.get("content", "").strip()
                if content:
                    content = content.replace("\n", " ")
                lines.append(f"- ({kind}:{ref}) {content[:200]}")
            return "\n".join(lines)
        except Exception:
            return ""

    async def _maybe_compress_context(self, state_obj: GameState) -> None:
        """当日志过长时，对较早的对话进行摘要压缩，并只保留最近若干条。

        策略：
        - 日志条数超过 14 条
        - 且距离上次摘要 >= 3 回合
        则对“最旧的 N-8 条”生成摘要，写入 metadata.log_summary，并仅保留最近 8 条至 state.log。
        """
        try:
            logs = state_obj.log or []
            if len(logs) <= 14:
                return

            turn_no = getattr(state_obj, "turn_number", 0)
            last_sum_turn = state_obj.metadata.get("last_summary_turn", -999)
            if turn_no - last_sum_turn < 3:
                return

            # 切分：旧日志 = 除去最后 8 条
            keep_recent = 8
            old_logs = logs[:-keep_recent]
            recent_logs = logs[-keep_recent:]

            # 构建待摘要文本
            def fmt(entry):
                try:
                    return f"[{entry.actor}] {entry.text}"
                except Exception:
                    # 字典或其他
                    actor = getattr(entry, "actor", None) or entry.get("actor", "?")
                    text = getattr(entry, "text", None) or entry.get("text", "")
                    return f"[{actor}] {text}"

            old_text = "\n".join(fmt(e) for e in old_logs)[-6000:]

            # 调用同一模型做简要摘要（成本可控，且减少后续回合 token）
            prompt = (
                "请将以下对话历史压缩为简洁要点，重点保留：场景进展、重要道具变化、NPC关系变化、未完成线索/任务。"
                "用 6-10 条要点中文输出，避免重复细节。\n\n" + old_text
            )
            resp = await self.model.ainvoke([
                {"role": "user", "content": prompt}
            ])
            summary = getattr(resp, "content", None) or ""

            # 写入 metadata + 世界变量（双处，便于不同路径引用）
            state_obj.metadata["log_summary"] = summary
            if "variables" not in state_obj.world.dict():
                state_obj.world.variables = state_obj.world.variables or {}
            state_obj.world.variables["conversation_summary"] = summary
            state_obj.metadata["last_summary_turn"] = turn_no

            # 仅保留最近日志，降低上下文
            state_obj.log = recent_logs
        except Exception as e:
            logger.debug(f"上下文压缩失败，忽略并继续: {e}")

    async def process_turn_sync(
        self, session_id: str, player_action: str, game_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理回合（非流式，返回与现有接口兼容的结果）"""
        # 将 dict → GameState，并设置到工具上下文
        try:
            state_obj = GameState(**game_state)
        except Exception:
            # 回退：若模型差异导致创建失败，则直接透传
            state_obj = None

        if state_obj is not None:
            set_state(state_obj)

        system_prompt = self._system_prompt(game_state)
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"玩家行动: {player_action}\n\n请作为DM处理该行动，必要时调用工具更新状态。",
            },
        ]

        config = {"configurable": {"thread_id": session_id}}

        # 上下文压缩（必要时）
        if state_obj is not None:
            await self._maybe_compress_context(state_obj)

        # 执行（非流式）
        try:
            # 注入世界检索片段
            kb = self._retrieve_snippets(player_action, game_state)
            if kb:
                messages.insert(1, {"role": "system", "content": kb})

            result = await self.agent.ainvoke({"messages": messages}, config=config)
        except Exception as e:
            logger.error(f"❌ LangGraph 执行失败: {e}")
            return {
                "narration": f"处理回合失败: {e}",
                "tool_calls": [],
                "updated_state": game_state,
                "turn": game_state.get("turn_number", 0),
                "error": str(e),
            }

        # 解析结果
        narration_parts: List[str] = []
        tool_calls: List[Dict[str, Any]] = []

        messages_out = result.get("messages", []) if isinstance(result, dict) else []
        for msg in messages_out:
            content = getattr(msg, "content", None) if hasattr(msg, "content") else msg.get("content")
            if content:
                narration_parts.append(content)

            # 工具调用（如有）
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append({
                        "tool": tc.get("name"),
                        "input": tc.get("args", {}),
                    })

        # 更新回合数
        new_state = dict(game_state)
        new_state["turn_number"] = new_state.get("turn_number", 0) + 1

        return {
            "narration": "\n\n".join(narration_parts) if narration_parts else "",
            "tool_calls": tool_calls,
            "updated_state": new_state,
            "turn": new_state["turn_number"],
        }

    async def process_turn(
        self, session_id: str, player_action: str, game_state: Dict[str, Any], checkpoint_id: Optional[str] = None
    ):
        """处理回合（改进流式）：优先尝试 LangGraph astream，失败则降级到同步分段"""
        # 将 dict → GameState，并设置到工具上下文
        try:
            state_obj = GameState(**game_state)
            set_state(state_obj)
        except Exception:
            pass

        # 压缩上下文（必要时）
        try:
            if state_obj is not None:
                await self._maybe_compress_context(state_obj)
                # 用压缩后的结构更新 game_state（以便后续 system_prompt 能读到摘要）
                game_state = state_obj.model_dump()
        except Exception:
            pass

        system_prompt = self._system_prompt(game_state)
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"玩家行动: {player_action}\n\n请作为DM处理该行动，必要时调用工具更新状态。",
            },
        ]

        config = {"configurable": {"thread_id": session_id}}
        if checkpoint_id:
            config["configurable"]["checkpoint_id"] = checkpoint_id

        # 注入世界检索片段
        kb = self._retrieve_snippets(player_action, game_state)
        if kb:
            messages.insert(1, {"role": "system", "content": kb})

        # 1) 尝试 LangGraph 原生流式
        try:
            # 优先使用 updates 模式（逐节点/逐步更新）
            async for event in self.agent.astream(
                {"messages": messages},
                config=config,
                stream_mode="updates",
            ):
                # 尝试从 updates 中提取最新消息
                try:
                    if isinstance(event, dict):
                        # event 可能是 {node_name: {"messages": [...]}} 或含有 values
                        for _, update in event.items():
                            if isinstance(update, dict) and "messages" in update and update["messages"]:
                                last = update["messages"][-1]
                                content = getattr(last, "content", None) if hasattr(last, "content") else last.get("content")
                                if content:
                                    # 检测是否为工具返回的中断信号
                                    try:
                                        import json as _json
                                        parsed = _json.loads(content) if isinstance(content, str) else None
                                    except Exception:
                                        parsed = None
                                    if isinstance(parsed, dict) and parsed.get("type") == "interrupt":
                                        # 从 graph 状态中提取 checkpoint_id（用于硬恢复）
                                        try:
                                            snap = self.agent.get_state(config)
                                            ckpt_id = snap.config.get("configurable", {}).get("checkpoint_id")
                                        except Exception:
                                            ckpt_id = None
                                        yield {
                                            "type": "interrupt",
                                            "prompt": parsed.get("question", "请选择"),
                                            "options": parsed.get("options", []),
                                            "checkpoint_id": ckpt_id,
                                        }
                                        return  # 中断，交给客户端 resume
                                    # 否则作为普通叙事片段
                                    yield {"type": "narration", "content": content}
                except Exception:
                    # 忽略解析错误
                    pass

            # 完成事件（附带线程内最终状态）
            # 这里不强取最终 state，沿用外部状态管理
            yield {"type": "complete", "content": {"ok": True}}
            return
        except Exception as e:
            logger.debug(f"LangGraph astream 不可用或出错，降级为同步分段: {e}")

        # 2) 降级：同步分段
        result = await self.process_turn_sync(session_id, player_action, game_state)
        narration = result.get("narration", "")
        if narration:
            yield {"type": "narration", "content": narration}
        for tc in result.get("tool_calls", []) or []:
            yield {"type": "tool_call", "content": tc}
        yield {"type": "complete", "content": result}


# 向后兼容命名
DMAgentLangGraph = DMGraphAgent
