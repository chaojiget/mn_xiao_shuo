"""
DM Agent API - 游戏主持人 Agent REST API
提供 DM Agent 的 HTTP 和 WebSocket 接口
"""

import asyncio
import json
import traceback
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/dm", tags=["dm"])

# 全局 DM Agent 实例
dm_agent = None


def init_dm_agent():
    """初始化 DM Agent"""
    global dm_agent
    import os

    from agents.dm_agent_langchain import DMAgentLangChain

    # 🔥 从环境变量读取模型名称
    # 优先使用 .env 中的配置，如果未设置则警告并使用 fallback
    model_name = os.getenv("DEFAULT_MODEL")
    if not model_name:
        logger.warning("⚠️  警告: DEFAULT_MODEL 环境变量未设置，使用 fallback: deepseek/deepseek-v3.1-terminus")
        model_name = "deepseek/deepseek-v3.1-terminus"

    # 🔥 启用 Checkpoint 模式，让 Agent 自动记忆对话历史
    dm_agent = DMAgentLangChain(
        model_name=model_name,
        use_checkpoint=True,
        checkpoint_db="data/checkpoints/dm.db"
    )
    logger.info(f"✅ DM Agent 已初始化 (模型: {model_name}, LangChain + Checkpoint)")


# ==================== 请求/响应模型 ====================

class DMActionRequest(BaseModel):
    """DM 处理玩家行动请求"""
    session_id: str = "default"
    player_action: str
    game_state: Dict[str, Any]


class DMActionResponse(BaseModel):
    """DM 处理结果"""
    success: bool
    narration: str
    tool_calls: list
    updated_state: Dict[str, Any]
    turn: int
    suggestions: list = []


class DMStateRequest(BaseModel):
    """获取 DM 状态请求"""
    session_id: str = "default"


# ==================== REST API 端点 ====================

@router.post("/action")
async def process_dm_action(request: DMActionRequest):
    """处理玩家行动（非流式）

    DM Agent 会分析玩家行动，调用相应工具，并生成场景描述

    Args:
        request: 包含 session_id, player_action, game_state

    Returns:
        {
            "success": true,
            "narration": str,
            "tool_calls": [...],
            "updated_state": {...},
            "turn": int,
            "suggestions": [...]
        }
    """
    if not dm_agent:
        raise HTTPException(status_code=500, detail="DM Agent 未初始化")

    try:
        result = await dm_agent.process_turn_sync(
            session_id=request.session_id,
            player_action=request.player_action,
            game_state=request.game_state
        )

        return {
            "success": True,
            **result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DM 处理失败: {str(e)}")


@router.get("/state/{session_id}")
async def get_dm_state(session_id: str):
    """获取 DM 当前状态

    Args:
        session_id: 会话ID

    Returns:
        {
            "success": true,
            "session_id": str,
            "status": str,
            "available_tools": [...]
        }
    """
    if not dm_agent:
        raise HTTPException(status_code=500, detail="DM Agent 未初始化")

    try:
        # 获取 DM Agent 配置信息
        return {
            "success": True,
            "session_id": session_id,
            "status": "active",
            "available_tools": dm_agent.base_options.allowed_tools if dm_agent.base_options else []
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 DM 状态失败: {str(e)}")


@router.post("/reset/{session_id}")
async def reset_dm_session(session_id: str):
    """重置 DM 会话

    Args:
        session_id: 会话ID

    Returns:
        {
            "success": true,
            "message": str
        }
    """
    if not dm_agent:
        raise HTTPException(status_code=500, detail="DM Agent 未初始化")

    try:
        # 清除会话相关的状态（如果有）
        from ..agents.game_tools_mcp import set_session
        set_session(session_id)

        return {
            "success": True,
            "message": f"会话 {session_id} 已重置"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置会话失败: {str(e)}")


# ==================== WebSocket 实时游戏 ====================

@router.websocket("/ws/{session_id}")
async def dm_websocket(websocket: WebSocket, session_id: str):
    """WebSocket 实时 DM 交互（增强版）

    客户端发送:
    {
        "type": "action",  // 玩家行动
        "player_action": str,
        "game_state": {...}
    }
    或
    {
        "type": "cancel"  // 取消当前生成
    }
    或
    {
        "type": "ping"  // 心跳检测
    }

    服务端返回（流式）:
    {
        "type": "narration" | "tool_call" | "tool_result" | "complete" | "error",
        "content": str | {...}
    }
    """
    if not dm_agent:
        await websocket.close(code=1011, reason="DM Agent 未初始化")
        return

    await websocket.accept()
    logger.info(f"[DM WebSocket] 会话 {session_id} 已连接")

    # 取消事件（用于中断流式生成）
    cancel_event = asyncio.Event()
    current_task = None

    # 心跳任务
    async def heartbeat():
        """定期发送心跳，检测连接状态"""
        try:
            while True:
                await asyncio.sleep(30)  # 每30秒发送一次心跳
                try:
                    await websocket.send_json({"type": "heartbeat", "timestamp": asyncio.get_event_loop().time()})
                except Exception as e:
                    logger.warning(f"[DM WebSocket] 心跳发送失败: {e}")
                    break
        except asyncio.CancelledError:
            pass

    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        while True:
            # 接收客户端消息
            try:
                raw_message = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
            except asyncio.TimeoutError:
                # 60秒无消息，发送ping检测连接
                try:
                    await websocket.send_json({"type": "ping"})
                    continue
                except:
                    logger.warning(f"[DM WebSocket] 连接超时")
                    break

            message = json.loads(raw_message)
            msg_type = message.get("type")

            if msg_type == "action":
                player_action = message.get("player_action")
                game_state = message.get("game_state", {})

                logger.info(f"[DM WebSocket] 收到行动: {player_action[:50]}...")

                # 重置取消事件
                cancel_event.clear()

                # 流式处理
                try:
                    async for event in dm_agent.process_turn(
                        session_id=session_id,
                        player_action=player_action,
                        game_state=game_state
                    ):
                        # 检查是否取消
                        if cancel_event.is_set():
                            logger.info(f"[DM WebSocket] 生成已取消")
                            await websocket.send_json({
                                "type": "cancelled",
                                "message": "生成已被用户取消"
                            })
                            break

                        # 发送事件到客户端
                        await websocket.send_json(event)

                except asyncio.CancelledError:
                    logger.info(f"[DM WebSocket] 生成被取消")
                    await websocket.send_json({
                        "type": "cancelled",
                        "message": "生成已被取消"
                    })

                except Exception as e:
                    logger.error(f"[DM WebSocket] 处理回合错误: {e}")
                    traceback.print_exc()
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e)
                    })

            elif msg_type == "cancel":
                # 取消当前生成
                logger.info(f"[DM WebSocket] 收到取消请求")
                cancel_event.set()
                if current_task and not current_task.done():
                    current_task.cancel()
                await websocket.send_json({
                    "type": "cancelled",
                    "message": "生成已取消"
                })

            elif msg_type == "ping":
                # 心跳检测
                await websocket.send_json({"type": "pong", "timestamp": asyncio.get_event_loop().time()})

            else:
                # 未知消息类型
                logger.warning(f"[DM WebSocket] 未知消息类型: {msg_type}")
                await websocket.send_json({
                    "type": "error",
                    "error": f"未知消息类型: {msg_type}"
                })

    except WebSocketDisconnect:
        logger.info(f"[DM WebSocket] 会话 {session_id} 断开连接")

    except Exception as e:
        logger.error(f"[DM WebSocket] 错误: {e}")
        traceback.print_exc()

        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        except:
            pass

    finally:
        # 清理
        heartbeat_task.cancel()
        if current_task and not current_task.done():
            current_task.cancel()

        try:
            await websocket.close()
        except:
            pass

        logger.info(f"[DM WebSocket] 会话 {session_id} 已清理")


# ==================== 工具信息端点 ====================

@router.get("/tools")
async def get_dm_tools():
    """获取 DM Agent 可用的工具列表

    Returns:
        {
            "success": true,
            "tools": [
                {
                    "name": str,
                    "description": str
                },
                ...
            ]
        }
    """
    if not dm_agent:
        raise HTTPException(status_code=500, detail="DM Agent 未初始化")

    try:
        # 获取工具列表
        tools = dm_agent.base_options.allowed_tools if dm_agent.base_options else []

        # 简化工具信息（去掉 mcp__game__ 前缀）
        tool_info = []
        for tool_name in tools:
            display_name = tool_name.replace("mcp__game__", "")
            tool_info.append({
                "name": display_name,
                "full_name": tool_name,
                "description": f"游戏工具: {display_name}"
            })

        return {
            "success": True,
            "tools": tool_info,
            "count": len(tool_info)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")


@router.get("/health")
async def dm_health_check():
    """健康检查端点

    Returns:
        {
            "status": str,
            "dm_agent_initialized": bool
        }
    """
    return {
        "status": "ok" if dm_agent else "dm_agent_not_initialized",
        "dm_agent_initialized": dm_agent is not None
    }
