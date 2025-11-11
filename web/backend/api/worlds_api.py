"""
世界包管理 API (WorldPack System)
处理世界生成、查询、校验、快照等操作
"""

import gzip
import json
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.world_generation_job import create_world_generation_job
from services.world_indexer import create_world_indexer
from services.world_validator import WorldValidator
from services.pacing_presets import PacingPresets
from services.writing_style_presets import WritingStylePresets

from models.world_pack import WorldGenerationRequest, WorldPack

router = APIRouter(prefix="/api/worlds", tags=["worlds"])


# 全局路径
def get_db_path() -> str:
    project_root = Path(__file__).parent.parent.parent.parent
    return str(project_root / "data" / "sqlite" / "novel.db")


# ============ 请求/响应模型 ============


class GenerateWorldResponse(BaseModel):
    job_id: str
    world_id: str
    status: str


class SnapshotRequest(BaseModel):
    tag: str


# ============ API 端点 ============


@router.post("/generate", response_model=GenerateWorldResponse)
async def generate_world(request: WorldGenerationRequest, background_tasks: BackgroundTasks):
    """
    触发世界生成

    Returns:
        GenerateWorldResponse: 任务信息
    """
    from llm.langchain_backend import LangChainBackend

    db_path = get_db_path()

    # 创建 LLM 客户端
    llm_client = LangChainBackend()

    # 创建生成任务
    job = await create_world_generation_job(
        request=request, llm_client=llm_client, db_path=db_path, progress_callback=None
    )

    # 在后台执行
    background_tasks.add_task(job.run)

    return GenerateWorldResponse(job_id=job.job_id, world_id=job.world_id, status="QUEUED")


@router.get("/{world_id}/status")
async def get_generation_status(world_id: str):
    """查询世界生成状态"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT phase, progress, error, updated_at
            FROM world_generation_jobs
            WHERE world_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
        """,
            (world_id,),
        )

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="任务不存在")

        phase, progress, error, updated_at = row

        return {
            "world_id": world_id,
            "phase": phase,
            "progress": progress,
            "error": error,
            "updated_at": updated_at,
        }

    finally:
        conn.close()


@router.get("/{world_id}")
async def get_world(world_id: str):
    """获取世界包（解压）"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT json_gz FROM worlds WHERE id = ?
        """,
            (world_id,),
        )

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="世界不存在")

        json_gz = row[0]

        # 解压
        json_str = gzip.decompress(json_gz).decode("utf-8")

        # 返回 JSON
        return JSONResponse(content=json.loads(json_str))

    finally:
        conn.close()


@router.post("/{world_id}/validate")
async def validate_world(world_id: str):
    """校验世界"""
    db_path = get_db_path()

    # 获取世界
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT json_gz FROM worlds WHERE id = ?", (world_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="世界不存在")

        json_gz = row[0]
        json_str = gzip.decompress(json_gz).decode("utf-8")
        world_pack = WorldPack.model_validate_json(json_str)

    finally:
        conn.close()

    # 校验
    validator = WorldValidator()
    problems = validator.validate_all(world_pack)
    summary = validator.get_summary()

    return {
        "ok": not validator.has_errors(),
        "summary": summary,
        "problems": [
            {
                "severity": p.severity,
                "category": p.category,
                "message": p.message,
                "entity_id": p.entity_id,
            }
            for p in problems
        ],
    }


@router.post("/{world_id}/snapshot")
async def create_snapshot(world_id: str, request: SnapshotRequest):
    """创建世界快照"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 获取世界数据
        cursor.execute("SELECT json_gz FROM worlds WHERE id = ?", (world_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="世界不存在")

        json_gz = row[0]

        # 创建快照
        cursor.execute(
            """
            INSERT INTO world_snapshots (world_id, tag, json_gz)
            VALUES (?, ?, ?)
        """,
            (world_id, request.tag, json_gz),
        )

        snapshot_id = cursor.lastrowid
        conn.commit()

        return {"snapshot_id": snapshot_id, "world_id": world_id, "tag": request.tag}

    finally:
        conn.close()


@router.get("/{world_id}/snapshots")
async def list_snapshots(world_id: str):
    """列出世界快照"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, tag, created_at
            FROM world_snapshots
            WHERE world_id = ?
            ORDER BY created_at DESC
        """,
            (world_id,),
        )

        snapshots = []
        for row in cursor.fetchall():
            snapshot_id, tag, created_at = row
            snapshots.append({"id": snapshot_id, "tag": tag, "created_at": created_at})

        return {"snapshots": snapshots}

    finally:
        conn.close()


@router.post("/{world_id}/publish")
async def publish_world(world_id: str):
    """发布世界为默认世界"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 更新世界状态
        cursor.execute(
            """
            UPDATE worlds SET status = 'published' WHERE id = ?
        """,
            (world_id,),
        )

        # 设置为默认世界
        cursor.execute(
            """
            INSERT INTO system_config (key, value)
            VALUES ('default_world_id', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
            (world_id,),
        )

        conn.commit()

        return {"status": "published", "world_id": world_id}

    finally:
        conn.close()


@router.get("/")
async def list_worlds():
    """列出所有世界"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, title, seed, status, created_at
            FROM worlds
            ORDER BY created_at DESC
        """
        )

        worlds = []
        for row in cursor.fetchall():
            world_id, title, seed, status, created_at = row
            worlds.append(
                {
                    "id": world_id,
                    "title": title,
                    "seed": seed,
                    "status": status,
                    "created_at": created_at,
                }
            )

        return {"worlds": worlds}

    finally:
        conn.close()


@router.get("/{world_id}/search")
async def search_world(world_id: str, query: str, kind: Optional[str] = None, top_k: int = 5):
    """语义搜索世界知识库"""
    db_path = get_db_path()

    indexer = create_world_indexer(db_path)
    results = indexer.search(world_id, query, kind, top_k)

    return {"results": results}


@router.get("/{world_id}/stats")
async def get_world_stats(world_id: str):
    """获取世界统计信息"""
    db_path = get_db_path()

    indexer = create_world_indexer(db_path)
    stats = indexer.get_stats(world_id)

    return stats


# ============ 节奏预设 API ============


@router.get("/pacing/presets")
async def list_pacing_presets():
    """
    列出所有可用的节奏预设

    Returns:
        dict: 预设名称和详细信息
    """
    return PacingPresets.list_presets()


@router.get("/pacing/presets/{preset_name}")
async def get_pacing_preset(preset_name: str):
    """
    获取特定节奏预设的配置

    Args:
        preset_name: 预设名称（action/literary/epic/horror/detective/slice_of_life/balanced）

    Returns:
        PacingControl: 节奏配置对象
    """
    try:
        preset = PacingPresets.get_preset(preset_name)
        return preset.dict()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"预设不存在: {preset_name}")


# ============ 文风预设 API ============


@router.get("/writing-style/presets")
async def list_writing_style_presets():
    """
    列出所有可用的文风预设

    Returns:
        dict: 预设名称和详细信息
    """
    return WritingStylePresets.list_presets()


@router.get("/writing-style/presets/{preset_name}")
async def get_writing_style_preset(preset_name: str):
    """
    获取特定文风预设的配置

    Args:
        preset_name: 预设名称（如 web_novel_cool, classical_elegant 等）

    Returns:
        WritingStyle: 文风配置对象
    """
    try:
        preset = WritingStylePresets.get_preset(preset_name)
        return preset.dict()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"预设不存在: {preset_name}")
