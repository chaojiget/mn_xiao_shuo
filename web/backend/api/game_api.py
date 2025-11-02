"""
游戏API路由 - 处理游戏回合、状态管理
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import asyncio

from ..game.game_engine import GameEngine, GameTurnRequest, GameTurnResponse
from ..game.game_tools import GameState

router = APIRouter(prefix="/api/game", tags=["game"])

# 全局游戏引擎实例（在启动时注入LLM客户端）
game_engine: Optional[GameEngine] = None


def init_game_engine(llm_client, db_path: str = None):
    """初始化游戏引擎"""
    global game_engine
    game_engine = GameEngine(llm_client, db_path=db_path)


# ==================== 请求/响应模型 ====================

class InitGameRequest(BaseModel):
    storyId: Optional[str] = None
    playerConfig: Optional[Dict[str, Any]] = None


class GameTurnRequestModel(BaseModel):
    playerInput: str
    currentState: Dict[str, Any]  # GameState as dict


# ==================== API路由 ====================

@router.post("/init")
async def init_game(request: InitGameRequest):
    """初始化新游戏"""
    if not game_engine:
        raise HTTPException(status_code=500, detail="游戏引擎未初始化")

    try:
        state = game_engine.init_game(story_id=request.storyId)

        return {
            "success": True,
            "state": state.model_dump(),
            "narration": "欢迎来到这个充满冒险的世界！你站在广场中央，前方是未知的旅程...",
            "suggestions": [
                "查看背包",
                "环顾四周",
                "向北走",
                "查看任务"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化游戏失败: {str(e)}")


@router.post("/turn")
async def process_turn(request: GameTurnRequestModel):
    """处理游戏回合（非流式）"""
    if not game_engine:
        raise HTTPException(status_code=500, detail="游戏引擎未初始化")

    try:
        # 打印调试信息
        print(f"[DEBUG] 收到请求: playerInput={request.playerInput}")
        print(f"[DEBUG] currentState keys: {request.currentState.keys() if isinstance(request.currentState, dict) else 'not dict'}")

        # 将dict转换为GameState
        try:
            state = GameState(**request.currentState)
            print(f"[DEBUG] GameState created successfully")
        except Exception as e:
            print(f"[ERROR] 创建GameState失败: {e}")
            import traceback
            traceback.print_exc()
            raise

        turn_request = GameTurnRequest(
            playerInput=request.playerInput,
            currentState=state
        )
        print(f"[DEBUG] TurnRequest created")

        response = await game_engine.process_turn(turn_request)
        print(f"[DEBUG] Turn processed successfully")

        return {
            "success": True,
            "narration": response.narration,
            "actions": response.actions,
            "hints": response.hints,
            "suggestions": response.suggestions,
            "metadata": response.metadata,
            "updatedState": state.model_dump()
        }

    except Exception as e:
        print(f"[ERROR] 处理回合失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理回合失败: {str(e)}")


@router.post("/turn/stream")
async def process_turn_stream(request: GameTurnRequestModel):
    """处理游戏回合（流式）"""
    if not game_engine:
        raise HTTPException(status_code=500, detail="游戏引擎未初始化")

    async def generate():
        try:
            # 将dict转换为GameState
            state = GameState(**request.currentState)

            turn_request = GameTurnRequest(
                playerInput=request.playerInput,
                currentState=state
            )

            async for chunk in game_engine.process_turn_stream(turn_request):
                # 发送SSE格式数据
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

            # 发送最终状态
            yield f"data: {json.dumps({'type': 'state', 'state': state.model_dump()}, ensure_ascii=False)}\n\n"

        except Exception as e:
            error_data = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/state/{game_id}")
async def get_game_state(game_id: str):
    """获取游戏状态（从数据库）"""
    # TODO: 从数据库加载游戏状态
    raise HTTPException(status_code=501, detail="暂未实现数据库存储")


@router.post("/state/{game_id}")
async def save_game_state(game_id: str, state: Dict[str, Any]):
    """保存游戏状态到数据库"""
    # TODO: 保存游戏状态到数据库
    raise HTTPException(status_code=501, detail="暂未实现数据库存储")


@router.get("/tools")
async def get_available_tools():
    """获取可用工具列表"""
    from game_tools import GameTools
    return {
        "tools": GameTools.get_tool_definitions()
    }
