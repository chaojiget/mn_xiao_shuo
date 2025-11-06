"""
测试WorldPack世界生成功能（修复版）
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "web" / "backend"))

from models.world_pack import WorldGenerationRequest
from services.world_generation_job import WorldGenerationJob
from llm.langchain_backend import LangChainBackend


async def test_world_generation():
    """测试世界生成"""

    print("=" * 80)
    print("🎮 WorldPack 世界生成测试")
    print("=" * 80)

    # 创建请求
    request = WorldGenerationRequest(
        title="测试世界",
        seed=42,
        tone="epic",
        difficulty="normal",
        num_locations=3,  # 小规模测试
        num_npcs=5,
        num_quests=3
    )

    print(f"\n📝 生成参数:")
    print(f"   - 标题: {request.title}")
    print(f"   - 基调: {request.tone}")
    print(f"   - 难度: {request.difficulty}")
    print(f"   - 地点: {request.num_locations}")
    print(f"   - NPC: {request.num_npcs}")
    print(f"   - 任务: {request.num_quests}")
    print(f"   - 种子: {request.seed}")

    # 初始化LLM
    llm_config = {
        "model": "deepseek",
        "temperature": 0.7,
        "max_tokens": 4096
    }
    llm_client = LangChainBackend(llm_config)

    # 数据库路径
    db_path = project_root / "data" / "sqlite" / "novel.db"

    # 进度回调
    def progress_callback(phase: str, progress: float, message: str):
        bar_length = 30
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\r[{bar}] {progress*100:.0f}% - {phase}: {message}", end="", flush=True)

    # 创建生成任务
    job = WorldGenerationJob(
        request=request,
        llm_client=llm_client,
        db_path=str(db_path),
        progress_callback=progress_callback
    )

    print(f"\n\n🚀 开始生成世界...\n")

    try:
        # 执行生成
        world_pack = await job.run()

        print(f"\n\n✅ 世界生成成功！\n")
        print("=" * 80)
        print(f"📊 世界统计:")
        print(f"   - 标题: {world_pack.meta.title}")
        print(f"   - 地点数: {len(world_pack.locations)}")
        print(f"   - NPC数: {len(world_pack.npcs)}")
        print(f"   - 任务数: {len(world_pack.quests)}")
        print(f"   - Lore条目: {len(world_pack.lore)}")
        print("=" * 80)

        # 显示一些示例数据
        if world_pack.locations:
            print(f"\n📍 示例地点: {world_pack.locations[0].name}")
            print(f"   生态: {world_pack.locations[0].biome}")
            print(f"   POI数: {len(world_pack.locations[0].pois)}")

        if world_pack.npcs:
            print(f"\n👤 示例NPC: {world_pack.npcs[0].name}")
            print(f"   角色: {world_pack.npcs[0].role}")
            print(f"   位置: {world_pack.npcs[0].home_location_id}")

        if world_pack.quests:
            print(f"\n📜 示例任务: {world_pack.quests[0].title}")
            print(f"   类型: {world_pack.quests[0].line}")
            print(f"   目标数: {len(world_pack.quests[0].objectives)}")

        print("\n✅ 测试通过！")
        return True

    except Exception as e:
        print(f"\n\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_world_generation())
    sys.exit(0 if success else 1)
