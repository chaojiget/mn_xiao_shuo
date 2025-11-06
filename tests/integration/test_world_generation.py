#!/usr/bin/env python3
"""
世界生成系统集成测试
测试 WorldGenerationJob 和 WorldValidator
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "web" / "backend"))

from models.world_pack import WorldGenerationRequest
from services.world_generation_job import create_world_generation_job
from services.world_validator import WorldValidator
from llm.langchain_backend import LangChainBackend


async def test_world_generation():
    """测试世界生成"""

    print("=" * 60)
    print("🧪 世界生成系统集成测试")
    print("=" * 60)

    # 1. 创建 LLM 客户端
    print("\n1️⃣ 初始化 LLM 客户端...")
    try:
        llm_client = LangChainBackend()
        print("   ✅ LLM 客户端初始化成功")
    except Exception as e:
        print(f"   ❌ LLM 客户端初始化失败: {e}")
        return

    # 2. 创建生成请求
    print("\n2️⃣ 创建世界生成请求...")
    request = WorldGenerationRequest(
        title="测试世界",
        seed=42,
        tone="epic",
        difficulty="normal",
        num_locations=5,
        num_npcs=8,
        num_quests=6
    )
    print(f"   📝 标题: {request.title}")
    print(f"   🎲 种子: {request.seed}")
    print(f"   🌍 地点数: {request.num_locations}")
    print(f"   👥 NPC数: {request.num_npcs}")
    print(f"   📋 任务数: {request.num_quests}")

    # 3. 创建生成任务
    print("\n3️⃣ 创建生成任务...")
    db_path = str(project_root / "data" / "sqlite" / "novel.db")

    async def progress_callback(phase, progress, message):
        bar_length = 30
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"   [{bar}] {progress*100:.0f}% - {phase}: {message}")

    job = await create_world_generation_job(
        request=request,
        llm_client=llm_client,
        db_path=db_path,
        progress_callback=progress_callback
    )

    print(f"   ✅ 任务创建成功: {job.job_id}")
    print(f"   🌍 世界ID: {job.world_id}")

    # 4. 执行生成
    print("\n4️⃣ 开始生成世界...")
    print("   " + "─" * 58)

    try:
        world_pack = await job.run()
        print("   " + "─" * 58)
        print("   ✅ 世界生成完成！")

    except Exception as e:
        print("   " + "─" * 58)
        print(f"   ❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. 显示生成结果
    print("\n5️⃣ 生成结果:")
    print(f"   🌍 世界: {world_pack.meta.title}")
    print(f"   🗺️  地点: {len(world_pack.locations)} 个")
    print(f"   👥 NPC: {len(world_pack.npcs)} 个")
    print(f"   📋 任务: {len(world_pack.quests)} 个")
    print(f"   🎁 掉落表: {len(world_pack.loot_tables)} 个")
    print(f"   ⚔️  遭遇表: {len(world_pack.encounter_tables)} 个")
    print(f"   📚 百科条目: {len(world_pack.lore)} 个")

    # 6. 详细信息
    print("\n6️⃣ 详细信息:")

    print("\n   📍 地点列表:")
    for i, loc in enumerate(world_pack.locations[:3], 1):
        print(f"      {i}. {loc.name} ({loc.biome}) @ ({loc.coord.x}, {loc.coord.y})")
        print(f"         - {len(loc.pois)} 个兴趣点, {len(loc.npcs)} 个 NPC")

    print("\n   👤 NPC 列表:")
    for i, npc in enumerate(world_pack.npcs[:3], 1):
        home = npc.home_location_id or "未知"
        print(f"      {i}. {npc.name} ({npc.role})")
        print(f"         - 位置: {home}")
        print(f"         - 性格: {npc.persona[:50]}...")

    print("\n   📋 任务列表:")
    for i, quest in enumerate(world_pack.quests[:3], 1):
        print(f"      {i}. {quest.title} [{quest.line}]")
        print(f"         - {len(quest.objectives)} 个目标")

    # 7. 校验世界
    print("\n7️⃣ 校验世界...")
    validator = WorldValidator()
    problems = validator.validate_all(world_pack)

    summary = validator.get_summary()
    print(f"   📊 校验结果: {summary['total']} 个问题")
    print(f"      ❌ 错误: {summary['errors']}")
    print(f"      ⚠️  警告: {summary['warnings']}")
    print(f"      ℹ️  信息: {summary['info']}")

    if problems:
        print("\n   问题详情:")
        for problem in problems[:10]:  # 只显示前10个
            print(f"      {problem}")

        if len(problems) > 10:
            print(f"      ... 还有 {len(problems) - 10} 个问题")

    # 8. 测试总结
    print("\n" + "=" * 60)
    if validator.has_errors():
        print("❌ 测试失败: 世界存在错误")
    else:
        print("✅ 测试通过: 世界生成成功且无错误")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_world_generation())
