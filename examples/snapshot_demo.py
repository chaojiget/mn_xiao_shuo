"""
Snapshot 快照机制演示

展示如何使用快照功能实现"时间旅行"和"悔棋"。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.sim.simulation import Simulation


def main():
    print("=" * 60)
    print("🎯 Snapshot 快照机制演示")
    print("=" * 60)
    print()

    # 创建模拟器
    print("📦 创建 Simulation...")
    sim = Simulation(seed=42, setting={"theme": "fantasy"})
    print(f"   初始状态: {sim}")
    print()

    # 场景 1: 基础快照与恢复
    print("=" * 60)
    print("场景 1: 基础快照与恢复")
    print("=" * 60)

    print("\n⏩ 运行 30 ticks...")
    sim.run(max_ticks=30)
    print(f"   当前状态: tick={sim.get_current_tick()}, events={sim.event_store.count()}")

    print("\n📸 创建快照 (checkpoint_30)...")
    checkpoint_30 = sim.snapshot()
    print(f"   快照: {checkpoint_30}")
    print(f"   快照内容: tick={checkpoint_30.tick}, events={len(checkpoint_30.events)}")

    print("\n⏩ 继续运行 20 ticks...")
    sim.run(max_ticks=20)
    print(f"   当前状态: tick={sim.get_current_tick()}, events={sim.event_store.count()}")

    print("\n⏪ 恢复到 checkpoint_30...")
    sim.restore(checkpoint_30)
    print(f"   恢复后状态: tick={sim.get_current_tick()}, events={sim.event_store.count()}")
    print("   ✅ 成功回到 tick=30！")

    # 场景 2: 多次快照（时间旅行）
    print("\n" + "=" * 60)
    print("场景 2: 多次快照（时间旅行）")
    print("=" * 60)

    # 重置模拟器
    sim.reset()
    print("\n🔄 重置模拟器...")

    # 创建多个存档点
    checkpoints = {}

    print("\n📸 创建多个存档点...")
    for i in [10, 20, 30, 40, 50]:
        sim.run(max_ticks=10)
        snapshot = sim.snapshot()
        checkpoints[i] = snapshot
        print(f"   Checkpoint {i}: tick={snapshot.tick}, events={len(snapshot.events)}")

    print(f"\n⏩ 继续运行到 tick=100...")
    sim.run(max_ticks=50)
    print(f"   当前状态: tick={sim.get_current_tick()}, events={sim.event_store.count()}")

    # 时间旅行到不同的存档点
    print("\n🕰️  时间旅行演示:")

    for target_tick in [30, 10, 50]:
        sim.restore(checkpoints[target_tick])
        print(f"   跳转到 tick={target_tick}: 当前状态 tick={sim.get_current_tick()}")

    # 场景 3: 快照元数据
    print("\n" + "=" * 60)
    print("场景 3: 快照元数据")
    print("=" * 60)

    snapshot = sim.snapshot()
    print("\n📋 快照元数据:")
    print(f"   Seed: {snapshot.metadata.get('seed')}")
    print(f"   Setting: {snapshot.metadata.get('setting')}")
    print(f"   Tick: {snapshot.tick}")
    print(f"   Events: {len(snapshot.events)}")
    print(f"   Clock State: {snapshot.clock_state}")

    # 场景 4: 快照独立性
    print("\n" + "=" * 60)
    print("场景 4: 快照独立性验证")
    print("=" * 60)

    print("\n📸 创建快照 A (tick=50)...")
    sim.restore(checkpoints[50])
    snapshot_a = sim.snapshot()
    print(f"   快照 A: tick={snapshot_a.tick}, events={len(snapshot_a.events)}")

    print("\n⏩ 继续运行 30 ticks...")
    sim.run(max_ticks=30)

    print(f"\n📸 创建快照 B (tick=80)...")
    snapshot_b = sim.snapshot()
    print(f"   快照 B: tick={snapshot_b.tick}, events={len(snapshot_b.events)}")

    print("\n🔍 验证快照独立性:")
    print(f"   快照 A 仍然是: tick={snapshot_a.tick}, events={len(snapshot_a.events)}")
    print(f"   快照 B 是: tick={snapshot_b.tick}, events={len(snapshot_b.events)}")
    print("   ✅ 快照之间完全独立！")

    # 场景 5: 实际应用场景
    print("\n" + "=" * 60)
    print("场景 5: 实际应用场景 - 游戏存档系统")
    print("=" * 60)

    print("\n🎮 模拟游戏存档系统:")

    # 重置
    sim.reset()

    save_slots = {}

    # 存档槽 1: 新手村
    print("\n   [存档槽 1] 新手村")
    sim.run(max_ticks=15)
    save_slots["slot1_newbie_village"] = sim.snapshot()
    print(f"      保存: tick={sim.get_current_tick()}")

    # 存档槽 2: 暗黑森林
    print("\n   [存档槽 2] 暗黑森林")
    sim.run(max_ticks=20)
    save_slots["slot2_dark_forest"] = sim.snapshot()
    print(f"      保存: tick={sim.get_current_tick()}")

    # 存档槽 3: 龙穴
    print("\n   [存档槽 3] 龙穴")
    sim.run(max_ticks=15)
    save_slots["slot3_dragon_lair"] = sim.snapshot()
    print(f"      保存: tick={sim.get_current_tick()}")

    # 模拟玩家死亡，加载存档
    print("\n   ⚠️  玩家在龙穴战斗中失败...")
    print("   ⏪ 加载存档槽 2（暗黑森林）...")
    sim.restore(save_slots["slot2_dark_forest"])
    print(f"      恢复到: tick={sim.get_current_tick()}")
    print("   ✅ 成功读档，重新挑战！")

    # 总结
    print("\n" + "=" * 60)
    print("✨ 演示完成！")
    print("=" * 60)
    print("\n📊 Snapshot 机制特性总结:")
    print("   ✅ 支持创建完整快照（时钟、调度器、事件历史）")
    print("   ✅ 支持恢复到任意时间点")
    print("   ✅ 支持多次快照（时间旅行）")
    print("   ✅ 快照之间完全独立（深拷贝）")
    print("   ✅ 包含元数据（seed, setting）")
    print("   ✅ 适用于游戏存档系统")
    print("\n🔜 下一步: Day 7 - Replay 回放机制")
    print()


if __name__ == "__main__":
    main()
