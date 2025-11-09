"""
Simulation + RNG 集成示例

展示如何使用 Simulation 和 SeededRNG 构建确定性的随机模拟。
这是 Phase 1.5 的核心示例代码。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.sim.simulation import Simulation
from src.sim.event_store import Event
from src.utils.rng import SeededRNG


def demo_basic_simulation():
    """基础示例：带随机性的确定性模拟"""
    print("=" * 60)
    print("示例 1: 基础确定性模拟")
    print("=" * 60)

    # 创建模拟器
    sim = Simulation(seed=42, setting={"world": "fantasy"})
    rng = SeededRNG(base_seed=sim.seed)

    results = []

    # 定义随机事件生成器
    def generate_random_event():
        tick = sim.get_current_tick()
        value = rng.randint(f"event/{tick}", 1, 100)
        results.append(value)

        print(f"  Tick {tick:3d}: Generated random value = {value}")

    # 调度 5 个随机事件
    for i in range(1, 6):
        sim.schedule_custom_task(when=i * 10, fn=generate_random_event)

    # 运行模拟
    sim.run(max_ticks=50)

    print(f"\n随机值序列: {results}")
    print(f"事件总数: {sim.event_store.count()}")
    print(f"当前 tick: {sim.get_current_tick()}")
    print()


def demo_combat_simulation():
    """战斗模拟示例：展示复杂随机逻辑"""
    print("=" * 60)
    print("示例 2: 战斗模拟")
    print("=" * 60)

    sim = Simulation(seed=123, setting={"combat_mode": "turn_based"})
    rng = SeededRNG(base_seed=sim.seed)

    # 战斗统计
    stats = {
        "total_attacks": 0,
        "hits": 0,
        "total_damage": 0,
        "critical_hits": 0
    }

    def combat_round():
        tick = sim.get_current_tick()
        round_num = tick // 10

        # 攻击检定（1d20）
        attack_roll = rng.randint(f"combat/round_{round_num}/attack", 1, 20)

        # 命中判定（需要 >= 10）
        hit = attack_roll >= 10

        # 暴击判定（20 点自然骰）
        critical = attack_roll == 20

        # 伤害计算
        damage = 0
        if hit:
            if critical:
                # 暴击伤害翻倍
                base_damage = rng.randint(f"combat/round_{round_num}/damage", 5, 15)
                damage = base_damage * 2
                stats["critical_hits"] += 1
            else:
                damage = rng.randint(f"combat/round_{round_num}/damage", 5, 15)

        # 更新统计
        stats["total_attacks"] += 1
        if hit:
            stats["hits"] += 1
            stats["total_damage"] += damage

        # 输出战斗日志
        hit_str = "暴击!" if critical else ("命中" if hit else "未命中")
        damage_str = f", 伤害 {damage}" if hit else ""
        print(f"  回合 {round_num:2d}: 攻击检定 {attack_roll:2d} -> {hit_str}{damage_str}")

        # 记录事件
        event = Event(
            tick=tick,
            actor="player",
            action="attack",
            payload={
                "round": round_num,
                "attack_roll": attack_roll,
                "hit": hit,
                "critical": critical,
                "damage": damage
            },
            seed=f"{sim.seed}/combat/{round_num}"
        )
        sim.append_event(event)

    # 10 个回合的战斗
    for i in range(1, 11):
        sim.schedule_custom_task(when=i * 10, fn=combat_round)

    # 运行模拟
    sim.run(max_ticks=100)

    # 输出战斗统计
    print(f"\n战斗统计:")
    print(f"  总攻击次数: {stats['total_attacks']}")
    print(f"  命中次数: {stats['hits']}")
    print(f"  命中率: {stats['hits'] / stats['total_attacks'] * 100:.1f}%")
    print(f"  暴击次数: {stats['critical_hits']}")
    print(f"  总伤害: {stats['total_damage']}")
    print(f"  平均伤害: {stats['total_damage'] / stats['hits']:.1f}" if stats['hits'] > 0 else "  平均伤害: 0")
    print()


def demo_npc_behavior():
    """NPC 行为模拟示例"""
    print("=" * 60)
    print("示例 3: NPC 行为模拟")
    print("=" * 60)

    sim = Simulation(seed=456, setting={"npc_count": 3})
    rng = SeededRNG(base_seed=sim.seed)

    # NPC 行为选项
    behaviors = ["巡逻", "闲置", "交谈", "交易", "睡觉"]

    npc_logs = {f"NPC_{i}": [] for i in range(1, 4)}

    def npc_decide_action(npc_id):
        def action():
            tick = sim.get_current_tick()

            # NPC 随机选择行为
            chosen = rng.choice(f"npc/{npc_id}/action/{tick}", behaviors)
            npc_logs[npc_id].append(chosen)

            print(f"  Tick {tick:3d}: {npc_id} 选择行为 -> {chosen}")

        return action

    # 为每个 NPC 调度行为
    for npc_id in npc_logs.keys():
        for i in range(1, 11):
            sim.schedule_custom_task(
                when=i * 5,
                fn=npc_decide_action(npc_id),
                label=f"{npc_id}_action_{i}"
            )

    # 运行模拟
    sim.run(max_ticks=50)

    # 统计每个 NPC 的行为
    print(f"\nNPC 行为统计:")
    for npc_id, actions in npc_logs.items():
        behavior_counts = {b: actions.count(b) for b in behaviors}
        print(f"  {npc_id}:")
        for behavior, count in behavior_counts.items():
            if count > 0:
                print(f"    {behavior}: {count} 次")
    print()


def demo_deterministic_replay():
    """确定性回放示例：证明相同 seed 产生相同结果"""
    print("=" * 60)
    print("示例 4: 确定性验证")
    print("=" * 60)

    def run_simulation(seed):
        """运行一个简单的模拟并返回结果"""
        sim = Simulation(seed=seed, setting={})
        rng = SeededRNG(base_seed=seed)

        results = []

        def collect_value():
            tick = sim.get_current_tick()
            value = rng.randint(f"value/{tick}", 1, 100)
            results.append(value)

        for i in range(1, 11):
            sim.schedule_custom_task(when=i * 5, fn=collect_value)

        sim.run(max_ticks=50)
        return results

    # 使用相同 seed 运行两次
    print("运行模拟 (seed=42)...")
    results1 = run_simulation(42)
    print(f"  结果 1: {results1}")

    print("\n再次运行模拟 (seed=42)...")
    results2 = run_simulation(42)
    print(f"  结果 2: {results2}")

    # 验证结果一致
    if results1 == results2:
        print("\n✅ 确定性验证通过！相同 seed 产生完全相同的结果。")
    else:
        print("\n❌ 确定性验证失败！")

    # 使用不同 seed 运行
    print("\n运行模拟 (seed=999)...")
    results3 = run_simulation(999)
    print(f"  结果 3: {results3}")

    if results1 != results3:
        print("\n✅ 不同 seed 产生不同结果，符合预期。")
    else:
        print("\n❌ 不同 seed 产生相同结果，不符合预期！")
    print()


def demo_simulation_stats():
    """模拟器统计示例"""
    print("=" * 60)
    print("示例 5: 模拟器统计信息")
    print("=" * 60)

    sim = Simulation(seed=789, setting={"test": True})
    rng = SeededRNG(base_seed=sim.seed)

    # 添加一些随机任务
    for i in range(1, 21):
        sim.schedule_custom_task(
            when=i * 5,
            fn=lambda: rng.randint(f"task/{sim.get_current_tick()}", 1, 100)
        )

    # 运行一半
    sim.run(max_ticks=50)

    # 查看统计
    sim_stats = sim.get_stats()
    rng_stats = rng.get_stats()

    print("模拟器统计:")
    print(f"  种子: {sim_stats['seed']}")
    print(f"  当前 tick: {sim_stats['current_tick']}")
    print(f"  总 tick 数: {sim_stats['total_ticks']}")
    print(f"  事件数: {sim_stats['event_count']}")
    print(f"  待执行任务: {sim_stats['pending_tasks']}")

    print(f"\nRNG 统计:")
    print(f"  基础种子: {rng_stats['base_seed']}")
    print(f"  使用的路径数: {rng_stats['total_paths']}")
    print(f"  最常用路径: {rng_stats['most_used_path']}")
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("Phase 1.5 - Simulation + RNG 集成示例")
    print("=" * 60)
    print()

    demo_basic_simulation()
    demo_combat_simulation()
    demo_npc_behavior()
    demo_deterministic_replay()
    demo_simulation_stats()

    print("=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
