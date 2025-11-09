"""
测试 Simulation + RNG 确定性集成

验证 Simulation 与 SeededRNG 集成后的确定性行为。
这是 Phase 1.5 Day 5 的核心验收测试。
"""

import sys
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.sim.simulation import Simulation
from src.sim.event_store import Event
from src.utils.rng import SeededRNG


class TestSimulationWithRNG:
    """测试 Simulation 与 RNG 集成"""

    def test_simulation_with_rng(self):
        """测试 Simulation 可以使用 RNG"""
        sim = Simulation(seed=42, setting={})
        rng = SeededRNG(base_seed=sim.seed)

        # 使用 RNG 生成随机事件
        def create_random_event():
            tick = sim.get_current_tick()
            value = rng.randint(f"event/{tick}", 1, 100)

            event = Event(
                tick=tick,
                actor="random",
                action="random_value",
                payload={"value": value},
                seed=f"{sim.seed}/{tick}"
            )
            sim.append_event(event)

        # 调度随机事件
        for i in range(1, 6):
            sim.schedule_custom_task(
                when=i * 10,
                fn=create_random_event,
                label=f"random_event_{i}"
            )

        # 运行
        sim.run(max_ticks=50)

        # 验证事件生成
        random_events = [e for e in sim.get_events() if e.actor == "random"]
        assert len(random_events) == 5

    def test_deterministic_with_randomness(self):
        """测试带随机性的确定性运行"""
        def run_simulation_with_rng(seed):
            sim = Simulation(seed=seed, setting={})
            rng = SeededRNG(base_seed=seed)

            results = []

            def generate_random_outcome():
                tick = sim.get_current_tick()
                # 使用 RNG 生成随机值
                value = rng.randint(f"outcome/{tick}", 1, 100)
                results.append(value)

            # 调度多个随机任务
            for i in range(1, 11):
                sim.schedule_custom_task(
                    when=i * 5,
                    fn=generate_random_outcome,
                    label=f"random_{i}"
                )

            sim.run(max_ticks=50)
            return results

        # 运行两次，验证结果完全一致
        results1 = run_simulation_with_rng(42)
        results2 = run_simulation_with_rng(42)

        assert results1 == results2
        assert len(results1) == 10

    def test_different_seeds_different_outcomes(self):
        """测试不同 seed 产生不同随机结果"""
        def run_simulation(seed):
            sim = Simulation(seed=seed, setting={})
            rng = SeededRNG(base_seed=seed)

            values = []

            def collect_random_value():
                tick = sim.get_current_tick()
                value = rng.randint(f"value/{tick}", 1, 1000)
                values.append(value)

            for i in range(1, 6):
                sim.schedule_custom_task(when=i * 10, fn=collect_random_value)

            sim.run(max_ticks=50)
            return values

        values_seed_42 = run_simulation(42)
        values_seed_43 = run_simulation(43)

        # 不同 seed 应该产生不同结果
        assert values_seed_42 != values_seed_43


class TestComplexScenarios:
    """测试复杂场景的确定性"""

    def test_combat_simulation(self):
        """测试战斗模拟的确定性"""
        def run_combat_simulation(seed):
            sim = Simulation(seed=seed, setting={})
            rng = SeededRNG(base_seed=seed)

            combat_log = []

            def combat_round():
                tick = sim.get_current_tick()
                round_num = tick // 10

                # 攻击检定
                attack_roll = rng.randint(f"combat/round_{round_num}/attack", 1, 20)
                hit = attack_roll >= 10

                # 伤害计算（如果命中）
                damage = 0
                if hit:
                    damage = rng.randint(f"combat/round_{round_num}/damage", 5, 15)

                combat_log.append({
                    "round": round_num,
                    "attack_roll": attack_roll,
                    "hit": hit,
                    "damage": damage
                })

                # 记录事件
                event = Event(
                    tick=tick,
                    actor="player",
                    action="attack",
                    payload={
                        "attack_roll": attack_roll,
                        "hit": hit,
                        "damage": damage
                    },
                    seed=f"{seed}/combat/{round_num}"
                )
                sim.append_event(event)

            # 10 个回合
            for i in range(1, 11):
                sim.schedule_custom_task(when=i * 10, fn=combat_round)

            sim.run(max_ticks=100)
            return combat_log

        # 运行两次，验证战斗日志完全一致
        log1 = run_combat_simulation(42)
        log2 = run_combat_simulation(42)

        assert log1 == log2
        assert len(log1) == 10

    def test_npc_behavior_simulation(self):
        """测试 NPC 行为的确定性"""
        def run_npc_simulation(seed):
            sim = Simulation(seed=seed, setting={})
            rng = SeededRNG(base_seed=seed)

            npc_actions = []

            def npc_decide_action():
                tick = sim.get_current_tick()

                # NPC 从多个行动中随机选择
                actions = ["patrol", "idle", "talk", "trade"]
                chosen_action = rng.choice(f"npc/action/{tick}", actions)

                npc_actions.append(chosen_action)

                # 记录事件
                event = Event(
                    tick=tick,
                    actor="npc_001",
                    action=chosen_action,
                    payload={},
                    seed=f"{seed}/npc/{tick}"
                )
                sim.append_event(event)

            # 每 5 ticks NPC 决定一次行动
            for i in range(1, 21):
                sim.schedule_custom_task(when=i * 5, fn=npc_decide_action)

            sim.run(max_ticks=100)
            return npc_actions

        # 验证确定性
        actions1 = run_npc_simulation(42)
        actions2 = run_npc_simulation(42)

        assert actions1 == actions2
        assert len(actions1) == 20

    def test_loot_generation_simulation(self):
        """测试战利品生成的确定性"""
        def run_loot_simulation(seed):
            sim = Simulation(seed=seed, setting={})
            rng = SeededRNG(base_seed=seed)

            all_loot = []

            def generate_loot():
                tick = sim.get_current_tick()

                # 战利品池
                loot_pool = [
                    "sword", "shield", "potion", "gold", "gem",
                    "armor", "scroll", "ring", "amulet", "boots"
                ]

                # 随机抽取 2-4 件战利品
                count = rng.randint(f"loot/count/{tick}", 2, 4)
                loot = rng.sample(f"loot/items/{tick}", loot_pool, count)

                all_loot.append(loot)

                # 记录事件
                event = Event(
                    tick=tick,
                    actor="chest",
                    action="open",
                    payload={"loot": loot},
                    seed=f"{seed}/loot/{tick}"
                )
                sim.append_event(event)

            # 生成 5 次战利品
            for i in range(1, 6):
                sim.schedule_custom_task(when=i * 20, fn=generate_loot)

            sim.run(max_ticks=100)
            return all_loot

        # 验证确定性
        loot1 = run_loot_simulation(42)
        loot2 = run_loot_simulation(42)

        assert loot1 == loot2
        assert len(loot1) == 5


class TestLongRunDeterminism:
    """测试长时间运行的确定性"""

    def test_1000_ticks_determinism(self):
        """测试 1000 ticks 的确定性"""
        def run_long_simulation(seed):
            sim = Simulation(seed=seed, setting={})
            rng = SeededRNG(base_seed=seed)

            checksum = 0

            def accumulate_random():
                tick = sim.get_current_tick()
                value = rng.randint(f"tick/{tick}", 1, 1000)
                nonlocal checksum
                checksum += value

            # 每 10 ticks 生成一个随机值
            for i in range(1, 101):
                sim.schedule_custom_task(when=i * 10, fn=accumulate_random)

            sim.run(max_ticks=1000)
            return checksum

        # 运行两次，验证校验和完全一致
        checksum1 = run_long_simulation(42)
        checksum2 = run_long_simulation(42)

        assert checksum1 == checksum2
        assert checksum1 > 0

    def test_complex_interleaved_randomness(self):
        """测试复杂交错随机性的确定性"""
        def run_complex_simulation(seed):
            sim = Simulation(seed=seed, setting={})
            rng = SeededRNG(base_seed=seed)

            results = {
                "attacks": [],
                "loot": [],
                "npc_actions": []
            }

            def attack_action():
                tick = sim.get_current_tick()
                roll = rng.randint(f"attack/{tick}", 1, 20)
                results["attacks"].append(roll)

            def loot_action():
                tick = sim.get_current_tick()
                items = ["a", "b", "c", "d"]
                item = rng.choice(f"loot/{tick}", items)
                results["loot"].append(item)

            def npc_action():
                tick = sim.get_current_tick()
                value = rng.random(f"npc/{tick}")
                results["npc_actions"].append(value)

            # 交错调度不同类型的随机事件
            for i in range(1, 51):
                if i % 3 == 0:
                    sim.schedule_custom_task(when=i * 2, fn=attack_action)
                elif i % 3 == 1:
                    sim.schedule_custom_task(when=i * 2, fn=loot_action)
                else:
                    sim.schedule_custom_task(when=i * 2, fn=npc_action)

            sim.run(max_ticks=100)
            return results

        # 验证复杂场景的确定性
        results1 = run_complex_simulation(42)
        results2 = run_complex_simulation(42)

        assert results1["attacks"] == results2["attacks"]
        assert results1["loot"] == results2["loot"]
        assert results1["npc_actions"] == results2["npc_actions"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
