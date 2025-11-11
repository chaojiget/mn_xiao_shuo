"""
游戏API路由 - 处理游戏回合、状态管理
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from game.game_engine import GameEngine, GameTurnRequest, GameTurnResponse
from game.game_tools import GameState
from pydantic import BaseModel
from services.save_service import SaveService
from utils.logger import get_logger

logger = get_logger(__name__)
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
    worldId: Optional[str] = None  # WorldPack ID
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
    """初始化新游戏

    支持两种模式：
    1. 使用worldId从WorldPack加载预生成世界
    2. 使用storyId创建默认世界
    """
    if not game_engine:
        raise HTTPException(status_code=500, detail="游戏引擎未初始化")

    try:
        # 如果提供了worldId，从WorldPack加载
        if request.worldId:
            from pathlib import Path

            from services.world_loader import WorldLoader

            # 获取数据库路径
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = project_root / "data" / "sqlite" / "novel.db"

            loader = WorldLoader(str(db_path))
            state = loader.load_and_convert(request.worldId)

            if not state:
                raise HTTPException(status_code=404, detail=f"世界包 {request.worldId} 不存在")

            # 获取世界信息用于叙事
            world_title = state.metadata.get("worldPackTitle", "神秘世界")
            world_tone = state.world.variables.get("world_tone", "epic")

            # 根据基调定制开场白
            first_location = state.map.nodes[0].name if state.map.nodes else "起点"
            tone_narrations = {
                "epic": f"欢迎来到{world_title}！史诗般的冒险即将开始。你站在{first_location}，感受到命运的召唤...",
                "dark": f"黑暗笼罩着{world_title}...你发现自己身处{first_location}，周围弥漫着不祥的气息...",
                "cozy": f"欢迎来到温馨的{world_title}！你站在{first_location}，阳光洒在身上，冒险即将开始！",
                "mystery": f"神秘的{world_title}向你敞开大门...你站在{first_location}，感觉这里隐藏着许多秘密...",
                "whimsical": f"进入奇幻的{world_title}！你出现在{first_location}，周围充满了魔法和惊喜..."
            }

            narration = tone_narrations.get(world_tone, tone_narrations["epic"])

            suggestions = [
                "环顾四周",
                "查看背包",
                "查看任务",
                f"探索{first_location}"
            ]

        else:
            # 默认模式
            state = game_engine.init_game(story_id=request.storyId)
            narration = "欢迎来到这个充满冒险的世界！你站在广场中央，前方是未知的旅程..."
            suggestions = [
                "查看背包",
                "环顾四周",
                "向北走",
                "查看任务"
            ]

        return {
            "success": True,
            "state": state.model_dump(),
            "narration": narration,
            "suggestions": suggestions
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化游戏失败: {str(e)}")


@router.post("/turn")
async def process_turn(request: GameTurnRequestModel):
    """处理游戏回合（非流式）"""
    if not game_engine:
        raise HTTPException(status_code=500, detail="游戏引擎未初始化")

    try:
        # 打印调试信息
        logger.debug(f"[DEBUG] 收到请求: playerInput={request.playerInput}")
        logger.debug(f"[DEBUG] currentState keys: {request.currentState.keys() if isinstance(request.currentState, dict) else 'not dict'}")

        # 将dict转换为GameState
        try:
            state = GameState(**request.currentState)
            logger.debug(f"[DEBUG] GameState created successfully")
        except Exception as e:
            logger.error(f"[ERROR] 创建GameState失败: {e}")
            import traceback
            traceback.print_exc()
            raise

        turn_request = GameTurnRequest(
            playerInput=request.playerInput,
            currentState=state
        )
        logger.debug(f"[DEBUG] TurnRequest created")

        response = await game_engine.process_turn(turn_request)
        logger.debug(f"[DEBUG] Turn processed successfully")

        # 自动保存游戏状态到数据库（写入 auto_saves 表，避免槽位约束冲突）
        if save_service:
            try:
                turn_no = state.world.time if hasattr(state, "world") else request.currentState.get("world", {}).get("time", 0)
                auto_save_id = save_service.auto_save(
                    user_id="default_user",
                    game_state=state.model_dump(),
                    turn_number=turn_no,
                )
                logger.debug(f"[DEBUG] 💾 自动保存成功: auto_save_id={auto_save_id}")
            except Exception as e:
                logger.error(f"[WARNING] 自动保存失败: {e}")
                # 不阻断游戏流程

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
        logger.error(f"[ERROR] 处理回合失败: {e}")
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

            # 🔥 从上下文获取最终状态（包含所有工具修改）
            from agents.game_tools_langchain import get_state_object
            try:
                final_state = get_state_object()  # 获取工具修改后的 GameState
                logger.debug(f"✅ 从上下文获取到最终状态，背包物品数: {len(final_state.player.inventory)}")
            except ValueError:
                # 如果上下文中没有 GameState，使用原始状态
                logger.warning("⚠️  上下文中没有 GameState，使用原始状态")
                final_state = state

            # 发送最终状态
            yield f"data: {json.dumps({'type': 'state', 'state': final_state.model_dump()}, ensure_ascii=False)}\n\n"

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
            # 没有自动保存记录时返回success: false，不抛出404
            return {
                "success": False,
                "message": "没有自动保存记录"
            }

        return {
            "success": True,
            **auto_save
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取自动保存失败: {str(e)}")


# ==================== 任务系统 API (Phase 2) ====================

class QuestObjectiveModel(BaseModel):
    """任务目标模型"""
    id: str
    description: str
    current: int = 0
    required: int = 1
    completed: bool = False


class CreateQuestRequest(BaseModel):
    """创建任务请求"""
    quest_id: Optional[str] = None
    quest_type: str = "main"
    title: str
    description: str
    level_requirement: int = 1
    objectives: List[Dict[str, Any]]
    rewards: Dict[str, Any]


class ActivateQuestRequest(BaseModel):
    """激活任务请求"""
    quest_id: str


class UpdateQuestProgressRequest(BaseModel):
    """更新任务进度请求"""
    quest_id: str
    objective_id: str
    amount: int = 1


@router.post("/quests")
async def create_quest(request: CreateQuestRequest):
    """创建新任务

    Args:
        request: 包含任务详细信息

    Returns:
        {
            "success": true,
            "quest_id": str,
            "message": str
        }
    """
    if not game_engine:
        raise HTTPException(status_code=500, detail="游戏引擎未初始化")

    try:
        # 调用游戏工具的 create_quest
        from agents.game_tools_langchain import create_quest

        result = create_quest.invoke({
            "title": request.title,
            "description": request.description,
            "objectives": request.objectives,
            "rewards": request.rewards,
            "quest_type": request.quest_type,
            "level_requirement": request.level_requirement
        })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/quests")
async def get_quests(status: Optional[str] = None):
    """获取任务列表

    Args:
        status: 可选，筛选任务状态 (available/active/completed/failed)

    Returns:
        {
            "success": true,
            "quests": [...],
            "count": int
        }
    """
    if not game_engine:
        raise HTTPException(status_code=500, detail="游戏引擎未初始化")

    try:
        from agents.game_tools_langchain import get_quests

        # LangChain tool 需要使用 .invoke() 方法
        if status:
            result = get_quests.invoke({"status": status})
        else:
            result = get_quests.invoke({})

        return {
            "success": True,
            **result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.post("/quests/{quest_id}/activate")
async def activate_quest(quest_id: str):
    """激活任务

    Args:
        quest_id: 任务ID

    Returns:
        {
            "success": true,
            "quest_id": str,
            "message": str
        }
    """
    if not game_engine:
        raise HTTPException(status_code=500, detail="游戏引擎未初始化")

    try:
        from agents.game_tools_langchain import activate_quest

        result = activate_quest.invoke({"quest_id": quest_id})

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"激活任务失败: {str(e)}")


@router.put("/quests/{quest_id}/progress")
async def update_quest_progress(quest_id: str, request: UpdateQuestProgressRequest):
    """更新任务目标进度

    Args:
        quest_id: 任务ID
        request: 包含 objective_id 和 amount

    Returns:
        {
            "success": true,
            "quest_id": str,
            "objective_id": str,
            "current": int,
            "required": int,
            "completed": bool,
            "message": str
        }
    """
    if not game_engine:
        raise HTTPException(status_code=500, detail="游戏引擎未初始化")

    try:
        from agents.game_tools_langchain import update_quest_objective

        result = update_quest_objective.invoke({
            "quest_id": quest_id,
            "objective_id": request.objective_id,
            "amount": request.amount
        })

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新任务进度失败: {str(e)}")


@router.post("/quests/{quest_id}/complete")
async def complete_quest(quest_id: str):
    """完成任务并发放奖励

    Args:
        quest_id: 任务ID

    Returns:
        {
            "success": true,
            "quest_id": str,
            "quest_title": str,
            "rewards": {...},
            "message": str
        }
    """
    if not game_engine:
        raise HTTPException(status_code=500, detail="游戏引擎未初始化")

    try:
        from agents.game_tools_langchain import complete_quest

        result = complete_quest.invoke({"quest_id": quest_id})

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"完成任务失败: {str(e)}")


# ==================== NPC 系统 API (Phase 2) ====================

class CreateNPCRequest(BaseModel):
    """创建NPC请求"""
    npc_id: str
    name: str
    role: str
    description: str = ""
    location: str
    personality_traits: List[str] = []
    speech_style: str = ""
    goals: List[str] = []


class UpdateNPCRelationshipRequest(BaseModel):
    """更新NPC关系请求"""
    npc_id: str
    affinity_delta: int = 0
    trust_delta: int = 0
    reason: str = ""


class AddNPCMemoryRequest(BaseModel):
    """添加NPC记忆请求"""
    npc_id: str
    event_type: str  # conversation, quest, combat, observation
    summary: str
    emotional_impact: int = 0


@router.post("/npcs")
async def create_npc(request: CreateNPCRequest):
    """创建新NPC

    Args:
        request: NPC详细信息

    Returns:
        {
            "success": true,
            "npc_id": str,
            "name": str,
            "message": str
        }
    """
    if not game_engine:
        raise HTTPException(status_code=500, detail="游戏引擎未初始化")

    try:
        from agents.game_tools_langchain import create_npc

        result = create_npc.invoke({
            "npc_id": request.npc_id,
            "name": request.name,
            "role": request.role,
            "location": request.location,
            "description": request.description,
            "personality_traits": request.personality_traits,
            "speech_style": request.speech_style,
            "goals": request.goals
        })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建NPC失败: {str(e)}")


@router.get("/npcs")
async def get_npcs(location: Optional[str] = None, status: Optional[str] = None):
    """获取NPC列表

    Args:
        location: 可选，按位置筛选
        status: 可选，按状态筛选 (active/inactive/retired)

    Returns:
        {
            "success": true,
            "npcs": [...],
            "count": int,
            "location": str
        }
    """
    if not game_engine:
        raise HTTPException(status_code=500, detail="游戏引擎未初始化")

    try:
        from agents.game_tools_langchain import get_npcs

        params = {}
        if location:
            params["location"] = location
        if status:
            params["status"] = status

        result = get_npcs.invoke(params)

        return {
            "success": True,
            **result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取NPC列表失败: {str(e)}")


@router.put("/npcs/{npc_id}/relationship")
async def update_npc_relationship(npc_id: str, request: UpdateNPCRelationshipRequest):
    """更新NPC与玩家的关系

    Args:
        npc_id: NPC ID
        request: 关系变化数据

    Returns:
        {
            "success": true,
            "npc_id": str,
            "npc_name": str,
            "affinity": int,
            "trust": int,
            "relationship_type": str,
            "changes": {...},
            "message": str
        }
    """
    if not game_engine:
        raise HTTPException(status_code=500, detail="游戏引擎未初始化")

    try:
        from agents.game_tools_langchain import update_npc_relationship

        result = update_npc_relationship.invoke({
            "npc_id": npc_id,
            "affinity_delta": request.affinity_delta,
            "trust_delta": request.trust_delta,
            "reason": request.reason
        })

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新NPC关系失败: {str(e)}")


@router.post("/npcs/{npc_id}/memories")
async def add_npc_memory(npc_id: str, request: AddNPCMemoryRequest):
    """为NPC添加记忆

    Args:
        npc_id: NPC ID
        request: 记忆数据

    Returns:
        {
            "success": true,
            "npc_id": str,
            "npc_name": str,
            "memory_count": int,
            "message": str
        }
    """
    if not game_engine:
        raise HTTPException(status_code=500, detail="游戏引擎未初始化")

    try:
        from agents.game_tools_langchain import add_npc_memory

        result = add_npc_memory.invoke({
            "npc_id": npc_id,
            "event_type": request.event_type,
            "summary": request.summary,
            "emotional_impact": request.emotional_impact
        })

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加NPC记忆失败: {str(e)}")
