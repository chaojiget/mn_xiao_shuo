"""
DM Agent API - 游戏主持人 Agent REST API
提供 DM Agent 的 HTTP 和 WebSocket 接口
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import asyncio

router = APIRouter(prefix="/api/dm", tags=["dm"])

# 全局 DM Agent 实例
dm_agent = None


def init_dm_agent():
    """初始化 DM Agent"""
    global dm_agent
    from agents.dm_agent_langchain import DMAgentLangChain
    dm_agent = DMAgentLangChain(model_name="deepseek/deepseek-v3.1-terminus")
    print("✅ DM Agent 已初始化 (LangChain)")


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
    """WebSocket 实时 DM 交互

    客户端发送:
    {
        "type": "action",
        "player_action": str,
        "game_state": {...}
    }

    服务端返回（流式）:
    {
        "type": "narration_chunk" | "tool_call" | "complete",
        "data": {...}
    }
    """
    if not dm_agent:
        await websocket.close(code=1011, reason="DM Agent 未初始化")
        return

    await websocket.accept()
    print(f"[DM WebSocket] 会话 {session_id} 已连接")

    try:
        while True:
            # 接收客户端消息
            raw_message = await websocket.receive_text()
            message = json.loads(raw_message)

            if message.get("type") == "action":
                player_action = message.get("player_action")
                game_state = message.get("game_state", {})

                print(f"[DM WebSocket] 收到行动: {player_action}")

                # 流式处理
                narration_parts = []
                tool_calls = []

                async for event in dm_agent.process_turn(
                    session_id=session_id,
                    player_action=player_action,
                    game_state=game_state
                ):
                    # 解析事件类型
                    if hasattr(event, 'type'):
                        if event.type == 'text':
                            # 文本块
                            chunk = {
                                "type": "narration_chunk",
                                "data": {"text": event.text}
                            }
                            narration_parts.append(event.text)
                            await websocket.send_json(chunk)

                        elif event.type == 'tool_use':
                            # 工具调用
                            tool_call = {
                                "tool": event.name,
                                "input": event.input
                            }
                            tool_calls.append(tool_call)

                            chunk = {
                                "type": "tool_call",
                                "data": tool_call
                            }
                            await websocket.send_json(chunk)

                        elif event.type == 'tool_result':
                            # 工具结果（可选：发送给客户端）
                            chunk = {
                                "type": "tool_result",
                                "data": {
                                    "tool": getattr(event, 'tool_name', ''),
                                    "result": getattr(event, 'content', '')
                                }
                            }
                            await websocket.send_json(chunk)

                # 更新回合数
                game_state['turn_number'] = game_state.get('turn_number', 0) + 1

                # 发送完成消息
                complete_message = {
                    "type": "complete",
                    "data": {
                        "narration": "\n\n".join(narration_parts),
                        "tool_calls": tool_calls,
                        "turn": game_state['turn_number'],
                        "updated_state": game_state
                    }
                }
                await websocket.send_json(complete_message)

            elif message.get("type") == "ping":
                # 心跳检测
                await websocket.send_json({"type": "pong"})

            else:
                # 未知消息类型
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"未知消息类型: {message.get('type')}"}
                })

    except WebSocketDisconnect:
        print(f"[DM WebSocket] 会话 {session_id} 断开连接")

    except Exception as e:
        print(f"[DM WebSocket] 错误: {e}")
        import traceback
        traceback.print_exc()

        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)}
            })
        except:
            pass

        await websocket.close(code=1011, reason=str(e))


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
