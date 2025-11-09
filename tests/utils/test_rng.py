"""
测试 SeededRNG 随机数生成器

测试确定性、隔离性、各种随机方法等。
"""

import sys
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.rng import SeededRNG


class TestSeededRNG:
    """测试 SeededRNG 基础功能"""

    def test_initialization(self):
        """测试初始化"""
        rng = SeededRNG(base_seed=42)

        assert rng.base_seed == 42
        assert len(rng.rngs) == 0

    def test_randint(self):
        """测试随机整数生成"""
        rng = SeededRNG(base_seed=42)

        value = rng.randint("test", 1, 100)

        # 验证范围
        assert 1 <= value <= 100
        assert isinstance(value, int)

    def test_random(self):
        """测试随机浮点数生成"""
        rng = SeededRNG(base_seed=42)

        value = rng.random("test")

        # 验证范围
        assert 0.0 <= value < 1.0
        assert isinstance(value, float)

    def test_choice(self):
        """测试随机选择"""
        rng = SeededRNG(base_seed=42)

        options = ["a", "b", "c", "d"]
        choice = rng.choice("test", options)

        # 验证选择在列表中
        assert choice in options

    def test_shuffle(self):
        """测试序列打乱"""
        rng = SeededRNG(base_seed=42)

        original = [1, 2, 3, 4, 5]
        shuffled = rng.shuffle("test", original)

        # 验证不修改原列表
        assert original == [1, 2, 3, 4, 5]

        # 验证元素相同但顺序可能不同
        assert sorted(shuffled) == sorted(original)

    def test_sample(self):
        """测试随机抽样"""
        rng = SeededRNG(base_seed=42)

        population = ["a", "b", "c", "d", "e"]
        sample = rng.sample("test", population, 3)

        # 验证抽样数量
        assert len(sample) == 3

        # 验证元素来自总体
        assert all(item in population for item in sample)

        # 验证无重复
        assert len(set(sample)) == 3

    def test_uniform(self):
        """测试均匀分布"""
        rng = SeededRNG(base_seed=42)

        value = rng.uniform("test", 10.0, 20.0)

        # 验证范围
        assert 10.0 <= value < 20.0
        assert isinstance(value, float)

    def test_gauss(self):
        """测试高斯分布"""
        rng = SeededRNG(base_seed=42)

        # 生成多个值，验证均值接近 mu
        values = [rng.gauss(f"test/{i}", 100, 15) for i in range(1000)]

        mean = sum(values) / len(values)

        # 均值应该接近 100（允许一定误差）
        assert 95 <= mean <= 105


class TestDeterminism:
    """测试确定性"""

    def test_same_seed_same_path_same_result(self):
        """测试相同 seed 和 path 产生相同结果"""
        rng1 = SeededRNG(base_seed=42)
        rng2 = SeededRNG(base_seed=42)

        # 生成随机数
        values1 = [rng1.randint("test", 1, 100) for _ in range(10)]
        values2 = [rng2.randint("test", 1, 100) for _ in range(10)]

        # 验证完全一致
        assert values1 == values2

    def test_different_seeds_different_results(self):
        """测试不同 seed 产生不同结果"""
        rng1 = SeededRNG(base_seed=42)
        rng2 = SeededRNG(base_seed=43)

        values1 = [rng1.randint("test", 1, 100) for _ in range(10)]
        values2 = [rng2.randint("test", 1, 100) for _ in range(10)]

        # 验证不同（极小概率相同，但不太可能）
        assert values1 != values2

    def test_different_paths_different_results(self):
        """测试不同 path 产生不同结果"""
        rng = SeededRNG(base_seed=42)

        values1 = [rng.randint("path1", 1, 100) for _ in range(10)]
        values2 = [rng.randint("path2", 1, 100) for _ in range(10)]

        # 验证不同
        assert values1 != values2

    def test_path_isolation(self):
        """测试路径隔离性"""
        rng = SeededRNG(base_seed=42)

        # 交替访问不同路径
        v1_1 = rng.randint("path1", 1, 100)
        v2_1 = rng.randint("path2", 1, 100)
        v1_2 = rng.randint("path1", 1, 100)
        v2_2 = rng.randint("path2", 1, 100)

        # 创建新的 RNG，验证路径隔离
        rng2 = SeededRNG(base_seed=42)
        v1_1_check = rng2.randint("path1", 1, 100)
        v1_2_check = rng2.randint("path1", 1, 100)

        # 验证相同路径产生相同序列（不受其他路径干扰）
        assert v1_1 == v1_1_check
        assert v1_2 == v1_2_check

    def test_deterministic_shuffle(self):
        """测试打乱的确定性"""
        rng1 = SeededRNG(base_seed=42)
        rng2 = SeededRNG(base_seed=42)

        original = list(range(20))

        shuffled1 = rng1.shuffle("test", original)
        shuffled2 = rng2.shuffle("test", original)

        # 验证相同
        assert shuffled1 == shuffled2

    def test_deterministic_choice(self):
        """测试选择的确定性"""
        rng1 = SeededRNG(base_seed=42)
        rng2 = SeededRNG(base_seed=42)

        options = ["option1", "option2", "option3", "option4"]

        choices1 = [rng1.choice("test", options) for _ in range(10)]
        choices2 = [rng2.choice("test", options) for _ in range(10)]

        # 验证相同
        assert choices1 == choices2


class TestStats:
    """测试统计功能"""

    def test_access_count(self):
        """测试访问计数"""
        rng = SeededRNG(base_seed=42)

        # 访问多次
        for i in range(5):
            rng.randint("path1", 1, 100)

        for i in range(3):
            rng.randint("path2", 1, 100)

        stats = rng.get_stats()

        assert stats["base_seed"] == 42
        assert stats["total_paths"] == 2
        assert stats["access_counts"]["path1"] == 5
        assert stats["access_counts"]["path2"] == 3
        assert stats["most_used_path"] == "path1"

    def test_reset_path(self):
        """测试路径重置"""
        rng = SeededRNG(base_seed=42)

        # 生成一些值
        v1 = rng.randint("test", 1, 100)
        v2 = rng.randint("test", 1, 100)

        # 重置路径
        rng.reset_path("test")

        # 再次生成，应该从头开始
        v3 = rng.randint("test", 1, 100)

        # v3 应该等于 v1（重新开始）
        assert v3 == v1

    def test_clear_all(self):
        """测试清空所有路径"""
        rng = SeededRNG(base_seed=42)

        # 使用多个路径
        rng.randint("path1", 1, 100)
        rng.randint("path2", 1, 100)

        assert len(rng.rngs) == 2

        # 清空
        rng.clear_all()

        assert len(rng.rngs) == 0
        assert len(rng._access_count) == 0

    def test_repr(self):
        """测试字符串表示"""
        rng = SeededRNG(base_seed=42)

        rng.randint("path1", 1, 100)
        rng.randint("path1", 1, 100)
        rng.randint("path2", 1, 100)

        repr_str = repr(rng)

        assert "base_seed=42" in repr_str
        assert "paths=2" in repr_str
        assert "total_calls=3" in repr_str


class TestRealWorldScenarios:
    """测试真实场景"""

    def test_combat_scenario(self):
        """测试战斗场景（骰子、伤害、暴击）"""
        rng = SeededRNG(base_seed=42)

        # 攻击检定
        attack_roll = rng.randint("combat/round_1/attack", 1, 20)
        assert 1 <= attack_roll <= 20

        # 伤害计算
        damage = rng.uniform("combat/round_1/damage", 5.0, 15.0)
        assert 5.0 <= damage < 15.0

        # 暴击判定
        is_critical = rng.random("combat/round_1/critical") < 0.1
        assert isinstance(is_critical, bool)

    def test_npc_generation_scenario(self):
        """测试 NPC 生成场景"""
        rng = SeededRNG(base_seed=42)

        # 随机名字
        first_names = ["Alice", "Bob", "Charlie", "David"]
        last_names = ["Smith", "Johnson", "Williams", "Brown"]

        first = rng.choice("npc/001/first_name", first_names)
        last = rng.choice("npc/001/last_name", last_names)

        assert first in first_names
        assert last in last_names

        # 随机属性（高斯分布）
        strength = int(rng.gauss("npc/001/strength", 10, 3))
        intelligence = int(rng.gauss("npc/001/intelligence", 10, 3))

        assert isinstance(strength, int)
        assert isinstance(intelligence, int)

    def test_loot_generation_scenario(self):
        """测试战利品生成场景"""
        rng = SeededRNG(base_seed=42)

        # 战利品池
        loot_pool = [
            "sword", "shield", "potion", "gold", "gem",
            "armor", "scroll", "ring", "amulet", "boots"
        ]

        # 随机抽取 3 件战利品
        loot = rng.sample("loot/chest_01", loot_pool, 3)

        assert len(loot) == 3
        assert all(item in loot_pool for item in loot)
        assert len(set(loot)) == 3  # 无重复

    def test_event_trigger_scenario(self):
        """测试事件触发场景"""
        rng = SeededRNG(base_seed=42)

        # 多个事件，各自独立的触发概率
        event_triggered = {}

        for event_id in ["event1", "event2", "event3"]:
            probability = rng.random(f"events/{event_id}/trigger")
            event_triggered[event_id] = probability < 0.3  # 30% 触发率

        # 验证每个事件都有独立的触发判定
        assert len(event_triggered) == 3

    def test_deterministic_replay(self):
        """测试确定性回放（完整场景）"""
        def run_simulation(seed):
            """模拟一个完整场景"""
            rng = SeededRNG(base_seed=seed)
            results = []

            # 10 个回合的战斗
            for round_num in range(1, 11):
                attack = rng.randint(f"combat/round_{round_num}/attack", 1, 20)
                damage = rng.uniform(f"combat/round_{round_num}/damage", 5.0, 15.0)
                results.append((round_num, attack, damage))

            return results

        # 运行两次，验证结果完全一致
        results1 = run_simulation(42)
        results2 = run_simulation(42)

        assert results1 == results2

        # 不同 seed 应该产生不同结果
        results3 = run_simulation(43)
        assert results1 != results3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
