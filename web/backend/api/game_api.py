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
from ..services.save_service import SaveService

router = APIRouter(prefix="/api/game", tags=["game"])

# 全局游戏引擎实例（在启动时注入LLM客户端）
game_engine: Optional[GameEngine] = None

# 全局存档服务实例
save_service: Optional[SaveService] = None


def init_game_engine(llm_client, db_path: str = None):
    """初始化游戏引擎和存档服务"""
    global game_engine, save_service
    game_engine = GameEngine(llm_client, db_path=db_path)

    # 初始化存档服务
    if db_path:
        save_service = SaveService(db_path)


# ==================== 请求/响应模型 ====================

class InitGameRequest(BaseModel):
    storyId: Optional[str] = None
    playerConfig: Optional[Dict[str, Any]] = None


class GameTurnRequestModel(BaseModel):
    playerInput: str
    currentState: Dict[str, Any]  # GameState as dict


class SaveGameRequest(BaseModel):
    """保存游戏请求"""
    user_id: str = "default_user"
    slot_id: int  # 1-10
    save_name: str
    game_state: Dict[str, Any]


class LoadGameRequest(BaseModel):
    """加载游戏请求"""
    save_id: int


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


# ==================== 存档系统 API (Phase 2) ====================

@router.post("/save")
async def save_game(request: SaveGameRequest):
    """保存游戏到存档槽位

    Args:
        request: 包含 user_id, slot_id (1-10), save_name, game_state

    Returns:
        {
            "success": true,
            "save_id": int,
            "slot_id": int,
            "save_name": str,
            "message": str
        }
    """
    if not save_service:
        raise HTTPException(status_code=500, detail="存档服务未初始化")

    try:
        save_id = save_service.save_game(
            user_id=request.user_id,
            slot_id=request.slot_id,
            save_name=request.save_name,
            game_state=request.game_state,
            auto_save=False
        )

        return {
            "success": True,
            "save_id": save_id,
            "slot_id": request.slot_id,
            "save_name": request.save_name,
            "message": f"游戏已保存到槽位 {request.slot_id}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存游戏失败: {str(e)}")


@router.get("/saves/{user_id}")
async def get_saves(user_id: str = "default_user"):
    """获取用户的所有存档列表

    Args:
        user_id: 用户ID，默认 "default_user"

    Returns:
        {
            "success": true,
            "saves": [
                {
                    "save_id": int,
                    "slot_id": int,
                    "save_name": str,
                    "metadata": {...},
                    "screenshot_url": str,
                    "created_at": str,
                    "updated_at": str
                },
                ...
            ]
        }
    """
    if not save_service:
        raise HTTPException(status_code=500, detail="存档服务未初始化")

    try:
        saves = save_service.get_saves(user_id)

        return {
            "success": True,
            "saves": saves
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取存档列表失败: {str(e)}")


@router.get("/save/{save_id}")
async def load_game(save_id: int):
    """加载游戏存档

    Args:
        save_id: 存档ID

    Returns:
        {
            "success": true,
            "game_state": {...},
            "metadata": {...},
            "save_info": {...}
        }
    """
    if not save_service:
        raise HTTPException(status_code=500, detail="存档服务未初始化")

    try:
        save_data = save_service.load_game(save_id)

        if not save_data:
            raise HTTPException(status_code=404, detail=f"存档 {save_id} 不存在")

        return {
            "success": True,
            **save_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载存档失败: {str(e)}")


@router.delete("/save/{save_id}")
async def delete_save(save_id: int):
    """删除存档

    Args:
        save_id: 存档ID

    Returns:
        {
            "success": true,
            "message": str
        }
    """
    if not save_service:
        raise HTTPException(status_code=500, detail="存档服务未初始化")

    try:
        deleted = save_service.delete_save(save_id)

        if not deleted:
            raise HTTPException(status_code=404, detail=f"存档 {save_id} 不存在")

        return {
            "success": True,
            "message": f"存档 {save_id} 已删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除存档失败: {str(e)}")


@router.get("/save/{save_id}/snapshots")
async def get_snapshots(save_id: int):
    """获取存档的所有快照

    Args:
        save_id: 存档ID

    Returns:
        {
            "success": true,
            "snapshots": [
                {
                    "snapshot_id": int,
                    "turn_number": int,
                    "created_at": str
                },
                ...
            ]
        }
    """
    if not save_service:
        raise HTTPException(status_code=500, detail="存档服务未初始化")

    try:
        snapshots = save_service.get_snapshots(save_id)

        return {
            "success": True,
            "snapshots": snapshots
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取快照列表失败: {str(e)}")


@router.get("/auto-save/{user_id}")
async def get_latest_auto_save(user_id: str = "default_user"):
    """获取最新的自动保存

    Args:
        user_id: 用户ID

    Returns:
        {
            "success": true,
            "auto_save_id": int,
            "game_state": {...},
            "turn_number": int,
            "created_at": str
        }
    """
    if not save_service:
        raise HTTPException(status_code=500, detail="存档服务未初始化")

    try:
        auto_save = save_service.get_latest_auto_save(user_id)

        if not auto_save:
            raise HTTPException(status_code=404, detail="没有自动保存记录")

        return {
            "success": True,
            **auto_save
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取自动保存失败: {str(e)}")
