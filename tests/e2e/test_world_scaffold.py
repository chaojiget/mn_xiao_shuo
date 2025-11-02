#!/usr/bin/env python3
"""
世界脚手架系统测试脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "web" / "backend"))

from web.backend.world_db import WorldDatabase
from web.backend.world_models import (
    WorldGenerationRequest, LocationRefinementRequest,
    AffordanceExtractionRequest
)
from web.backend.world_generator import WorldGenerator
from web.backend.scene_refinement import SceneRefinement
from web.backend.llm import create_backend
from web.backend.llm.config_loader import LLMConfigLoader


async def test_world_scaffold():
    """测试世界脚手架系统"""

    print("=" * 60)
    print("世界脚手架系统测试")
    print("=" * 60)

    # 1. 初始化LLM后端
    print("\n[1/7] 初始化LLM后端...")
    config_loader = LLMConfigLoader()
    backend_type = config_loader.get_backend_type()
    backend_config = config_loader.get_backend_config()
    llm_backend = create_backend(backend_type, backend_config)
    print(f"✅ LLM后端已初始化 (类型: {backend_type})")

    # 2. 初始化数据库
    print("\n[2/7] 初始化数据库...")
    db_path = Path(__file__).parent / "data" / "sqlite" / "novel.db"
    world_db = WorldDatabase(str(db_path))
    print(f"✅ 数据库已连接: {db_path}")

    # 3. 初始化生成器
    print("\n[3/7] 初始化生成器...")
    world_generator = WorldGenerator(llm_backend)
    scene_refinement = SceneRefinement(llm_backend, world_db)
    print("✅ 生成器已初始化")

    # 4. 生成世界
    print("\n[4/7] 生成测试世界...")
    request = WorldGenerationRequest(
        novelId="test-novel-001",
        theme="deep sea survival",
        tone="压抑、未知、孤独",
        novelType="scifi",
        numRegions=3,  # 少量区域用于测试
        locationsPerRegion=5,
        poisPerLocation=3
    )

    try:
        result = await world_generator.generate_world(request)
        world = result["world"]
        regions = result["regions"]
        factions = result["factions"]

        print(f"✅ 世界生成成功!")
        print(f"   - 世界名称: {world.name}")
        print(f"   - 区域数量: {len(regions)}")
        print(f"   - 派系数量: {len(factions)}")

        # 保存到数据库
        world_db.create_world(world)
        for region in regions:
            world_db.create_region(region)
        for faction in factions:
            world_db.create_faction(faction)

        print("✅ 世界已保存到数据库")

    except Exception as e:
        print(f"❌ 世界生成失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. 生成地点
    print("\n[5/7] 为第一个区域生成地点...")
    try:
        from web.backend.world_models import LocationGenerationRequest

        first_region = regions[0]
        loc_request = LocationGenerationRequest(
            region_id=first_region.id,
            count=2  # 只生成2个地点用于测试
        )

        locations = await world_generator.generate_locations(
            loc_request, first_region, world
        )

        print(f"✅ 地点生成成功!")
        for loc in locations:
            print(f"   - {loc.name} ({loc.type})")
            world_db.create_location(loc)

        print("✅ 地点已保存到数据库")

    except Exception as e:
        print(f"❌ 地点生成失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 6. 细化地点
    print("\n[6/7] 细化第一个地点...")
    try:
        first_location = locations[0]
        refine_request = LocationRefinementRequest(
            location_id=first_location.id,
            turn=0,
            target_detail_level=2,
            passes=["structure", "sensory", "affordance", "cinematic"]
        )

        world_style = world.style_bible.dict()

        refinement_result = await scene_refinement.refine_location(
            refine_request, world_style
        )

        print(f"✅ 地点细化成功!")
        print(f"   - 细化等级: {refinement_result.detail_level}")
        print(f"   - 细化层数: {len(refinement_result.layers)}")
        print(f"   - 可供性数量: {len(refinement_result.affordances)}")

        if refinement_result.narrative_text:
            print(f"\n叙事文本预览:")
            print("-" * 60)
            print(refinement_result.narrative_text[:200] + "...")
            print("-" * 60)

        if refinement_result.affordances:
            print(f"\n可供性列表:")
            for i, aff in enumerate(refinement_result.affordances[:3], 1):
                print(f"   {i}. {aff.get('verb', '')} {aff.get('object', '')}")
                if aff.get('risk'):
                    print(f"      ⚠️  {aff['risk']}")

    except Exception as e:
        print(f"❌ 地点细化失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 7. 提取可供性
    print("\n[7/7] 提取可供性...")
    try:
        aff_request = AffordanceExtractionRequest(
            location_id=first_location.id,
            character_state={
                "attributes": {"力量": 5, "察觉": 3},
                "inventory": ["撬棍", "火把"]
            }
        )

        aff_result = await scene_refinement.extract_affordances(aff_request)

        print(f"✅ 可供性提取成功!")
        print(f"   - 可供性数量: {len(aff_result.affordances)}")
        print(f"   - 建议动作数量: {len(aff_result.suggested_actions)}")

        if aff_result.suggested_actions:
            print(f"\n建议动作（UI chips）:")
            for action in aff_result.suggested_actions:
                print(f"   - {action}")

    except Exception as e:
        print(f"❌ 可供性提取失败: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("✅ 所有测试通过!")
    print("=" * 60)
    print(f"\n测试世界ID: {world.id}")
    print(f"数据库路径: {db_path}")
    print("\n你可以通过以下方式查看数据:")
    print(f"  sqlite3 {db_path}")
    print(f"  SELECT * FROM world_scaffolds WHERE id = '{world.id}';")


if __name__ == "__main__":
    asyncio.run(test_world_scaffold())
