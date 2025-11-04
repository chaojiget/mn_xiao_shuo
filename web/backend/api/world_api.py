"""
世界管理API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import asyncio

from models.world_models import (
    WorldScaffold, Region, Location, POI, Faction,
    WorldGenerationRequest, RegionGenerationRequest,
    LocationGenerationRequest, POIGenerationRequest,
    LocationRefinementRequest, AffordanceExtractionRequest,
    WorldGenerationResponse, RefinementResult, AffordanceResult,
    GenerationProgress
)
from database.world_db import WorldDatabase
from services.world_generator import WorldGenerator
from services.scene_refinement import SceneRefinement


router = APIRouter(prefix="/api/world", tags=["world"])


# 全局依赖（需要在main.py中注入）
_world_db: Optional[WorldDatabase] = None
_world_generator: Optional[WorldGenerator] = None
_scene_refinement: Optional[SceneRefinement] = None


def init_world_services(world_db: WorldDatabase, llm_client):
    """初始化世界服务（从main.py调用）"""
    global _world_db, _world_generator, _scene_refinement
    _world_db = world_db
    _world_generator = WorldGenerator(llm_client)
    _scene_refinement = SceneRefinement(llm_client, world_db)


def get_world_db() -> WorldDatabase:
    if _world_db is None:
        raise HTTPException(500, "WorldDatabase not initialized")
    return _world_db


def get_world_generator() -> WorldGenerator:
    if _world_generator is None:
        raise HTTPException(500, "WorldGenerator not initialized")
    return _world_generator


def get_scene_refinement() -> SceneRefinement:
    if _scene_refinement is None:
        raise HTTPException(500, "SceneRefinement not initialized")
    return _scene_refinement


# ============ 世界脚手架 ============

@router.post("/generate", response_model=WorldGenerationResponse)
async def generate_world(
    request: WorldGenerationRequest,
    generator: WorldGenerator = Depends(get_world_generator),
    db: WorldDatabase = Depends(get_world_db)
):
    """生成完整世界脚手架"""

    try:
        # 生成世界
        result = await generator.generate_world(request)

        # 保存到数据库
        db.create_world(result["world"])

        for region in result["regions"]:
            db.create_region(region)

        for faction in result["factions"]:
            db.create_faction(faction)

        # TODO: 保存style_vocabulary到数据库

        return WorldGenerationResponse(
            world=result["world"],
            regions=result["regions"],
            summary=f"成功生成世界 '{result['world'].name}'，包含 {len(result['regions'])} 个区域和 {len(result['factions'])} 个派系"
        )

    except Exception as e:
        raise HTTPException(500, f"生成世界失败: {str(e)}")


@router.get("/scaffold/{world_id}", response_model=WorldScaffold)
async def get_world(
    world_id: str,
    db: WorldDatabase = Depends(get_world_db)
):
    """获取世界脚手架"""

    world = db.get_world(world_id)
    if not world:
        raise HTTPException(404, f"世界不存在: {world_id}")

    return world


@router.get("/by-novel/{novel_id}", response_model=WorldScaffold)
async def get_world_by_novel(
    novel_id: str,
    db: WorldDatabase = Depends(get_world_db)
):
    """根据小说ID获取世界"""

    world = db.get_world_by_novel(novel_id)
    if not world:
        raise HTTPException(404, f"该小说尚未生成世界: {novel_id}")

    return world


@router.put("/scaffold/{world_id}", response_model=WorldScaffold)
async def update_world(
    world_id: str,
    world: WorldScaffold,
    db: WorldDatabase = Depends(get_world_db)
):
    """更新世界脚手架"""

    existing = db.get_world(world_id)
    if not existing:
        raise HTTPException(404, f"世界不存在: {world_id}")

    db.update_world(world)
    return world


# ============ 区域 ============

@router.get("/scaffold/{world_id}/regions", response_model=List[Region])
async def get_regions(
    world_id: str,
    db: WorldDatabase = Depends(get_world_db)
):
    """获取世界的所有区域"""

    regions = db.get_regions_by_world(world_id)
    return regions


@router.get("/region/{region_id}", response_model=Region)
async def get_region(
    region_id: str,
    db: WorldDatabase = Depends(get_world_db)
):
    """获取单个区域"""

    region = db.get_region(region_id)
    if not region:
        raise HTTPException(404, f"区域不存在: {region_id}")

    return region


@router.post("/region/generate", response_model=List[Region])
async def generate_regions(
    request: RegionGenerationRequest,
    generator: WorldGenerator = Depends(get_world_generator),
    db: WorldDatabase = Depends(get_world_db)
):
    """生成区域（额外生成）"""

    # 获取世界信息
    world = db.get_world(request.world_id)
    if not world:
        raise HTTPException(404, f"世界不存在: {request.world_id}")

    try:
        regions = await generator._generate_regions(
            world_id=request.world_id,
            count=request.count,
            theme=world.theme,
            novel_type="scifi"  # TODO: 从世界中获取
        )

        # 保存到数据库
        for region in regions:
            db.create_region(region)

        return regions

    except Exception as e:
        raise HTTPException(500, f"生成区域失败: {str(e)}")


# ============ 地点 ============

@router.get("/region/{region_id}/locations", response_model=List[Location])
async def get_locations(
    region_id: str,
    db: WorldDatabase = Depends(get_world_db)
):
    """获取区域的所有地点"""

    locations = db.get_locations_by_region(region_id)
    return locations


@router.get("/location/{location_id}", response_model=Location)
async def get_location(
    location_id: str,
    db: WorldDatabase = Depends(get_world_db)
):
    """获取单个地点"""

    location = db.get_location(location_id)
    if not location:
        raise HTTPException(404, f"地点不存在: {location_id}")

    return location


@router.post("/location/generate", response_model=List[Location])
async def generate_locations(
    request: LocationGenerationRequest,
    generator: WorldGenerator = Depends(get_world_generator),
    db: WorldDatabase = Depends(get_world_db)
):
    """生成地点"""

    # 获取区域信息
    region = db.get_region(request.region_id)
    if not region:
        raise HTTPException(404, f"区域不存在: {request.region_id}")

    # 获取世界信息
    world = db.get_world(region.world_id)
    if not world:
        raise HTTPException(404, f"世界不存在: {region.world_id}")

    try:
        locations = await generator.generate_locations(request, region, world)

        # 保存到数据库
        for location in locations:
            db.create_location(location)

        return locations

    except Exception as e:
        raise HTTPException(500, f"生成地点失败: {str(e)}")


@router.put("/location/{location_id}", response_model=Location)
async def update_location(
    location_id: str,
    location: Location,
    db: WorldDatabase = Depends(get_world_db)
):
    """更新地点"""

    existing = db.get_location(location_id)
    if not existing:
        raise HTTPException(404, f"地点不存在: {location_id}")

    db.update_location(location)
    return location


# ============ POI ============

@router.get("/location/{location_id}/pois", response_model=List[POI])
async def get_pois(
    location_id: str,
    db: WorldDatabase = Depends(get_world_db)
):
    """获取地点的所有POI"""

    pois = db.get_pois_by_location(location_id)
    return pois


@router.post("/poi/generate", response_model=List[POI])
async def generate_pois(
    request: POIGenerationRequest,
    generator: WorldGenerator = Depends(get_world_generator),
    db: WorldDatabase = Depends(get_world_db)
):
    """生成POI"""

    # 获取地点信息
    location = db.get_location(request.location_id)
    if not location:
        raise HTTPException(404, f"地点不存在: {request.location_id}")

    try:
        pois = await generator.generate_pois(request, location)

        # 保存到数据库
        for poi in pois:
            db.create_poi(poi)

        return pois

    except Exception as e:
        raise HTTPException(500, f"生成POI失败: {str(e)}")


# ============ 场景细化 ============

@router.post("/location/{location_id}/refine", response_model=RefinementResult)
async def refine_location(
    location_id: str,
    request: LocationRefinementRequest,
    refinement: SceneRefinement = Depends(get_scene_refinement),
    db: WorldDatabase = Depends(get_world_db)
):
    """细化地点（多Pass流水线）"""

    # 获取世界风格
    location = db.get_location(location_id)
    if not location:
        raise HTTPException(404, f"地点不存在: {location_id}")

    region = db.get_region(location.region_id)
    world = db.get_world(region.world_id)

    world_style = world.style_bible.dict()

    try:
        result = await refinement.refine_location(request, world_style)
        return result

    except Exception as e:
        raise HTTPException(500, f"细化地点失败: {str(e)}")


@router.post("/location/{location_id}/affordances", response_model=AffordanceResult)
async def extract_affordances(
    location_id: str,
    request: AffordanceExtractionRequest,
    refinement: SceneRefinement = Depends(get_scene_refinement)
):
    """提取可供性（运行时）"""

    try:
        result = await refinement.extract_affordances(request)
        return result

    except Exception as e:
        raise HTTPException(500, f"提取可供性失败: {str(e)}")


# ============ 派系 ============

@router.get("/scaffold/{world_id}/factions", response_model=List[Faction])
async def get_factions(
    world_id: str,
    db: WorldDatabase = Depends(get_world_db)
):
    """获取世界的所有派系"""

    factions = db.get_factions_by_world(world_id)
    return factions


# ============ 批量生成（完整流程） ============

@router.post("/scaffold/{world_id}/generate-all")
async def generate_all_for_world(
    world_id: str,
    locations_per_region: int = 8,
    pois_per_location: int = 5,
    generator: WorldGenerator = Depends(get_world_generator),
    db: WorldDatabase = Depends(get_world_db)
):
    """为世界生成所有内容（区域→地点→POI）"""

    world = db.get_world(world_id)
    if not world:
        raise HTTPException(404, f"世界不存在: {world_id}")

    try:
        # 获取所有区域
        regions = db.get_regions_by_world(world_id)

        total_locations = 0
        total_pois = 0

        # 为每个区域生成地点
        for region in regions:
            # 生成地点
            loc_request = LocationGenerationRequest(
                region_id=region.id,
                count=locations_per_region
            )
            locations = await generator.generate_locations(loc_request, region, world)

            for location in locations:
                db.create_location(location)
                total_locations += 1

                # 为每个地点生成POI
                poi_request = POIGenerationRequest(
                    location_id=location.id,
                    count=pois_per_location
                )
                pois = await generator.generate_pois(poi_request, location)

                for poi in pois:
                    db.create_poi(poi)
                    total_pois += 1

        return {
            "success": True,
            "world_id": world_id,
            "regions": len(regions),
            "locations": total_locations,
            "pois": total_pois
        }

    except Exception as e:
        raise HTTPException(500, f"批量生成失败: {str(e)}")
