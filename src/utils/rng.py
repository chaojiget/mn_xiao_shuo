"""
SeededRNG - 带种子的随机数生成器

提供确定性的随机数生成，支持命名子种子路径。
核心特性：
- 确定性：相同的 base_seed + path 总是产生相同的随机序列
- 隔离性：不同的 path 产生独立的随机序列
- 可重现性：可以通过保存 seed 和 path 完全重现随机结果
"""

import random
from typing import Any, List, TypeVar

T = TypeVar('T')


class SeededRNG:
    """
    带命名子种子的随机数生成器

    核心概念：
    - base_seed: 全局种子（通常来自 Simulation）
    - path: 种子路径（如 "npc/001/dialog" 或 "combat/round_5/damage"）
    - 组合种子：base_seed ⊕ hash(path) 确保确定性和隔离性

    Example:
        rng = SeededRNG(base_seed=42)

        # 不同路径产生不同的随机序列
        val1 = rng.randint("player/move", 1, 6)
        val2 = rng.randint("enemy/move", 1, 6)

        # 相同路径产生相同的序列
        rng2 = SeededRNG(base_seed=42)
        val3 = rng2.randint("player/move", 1, 6)
        assert val1 == val3  # 确定性
    """

    def __init__(self, base_seed: int):
        """
        初始化随机数生成器

        Args:
            base_seed: 全局基础种子
        """
        self.base_seed = base_seed
        self.rngs: dict[str, random.Random] = {}
        self._access_count: dict[str, int] = {}  # 记录每个路径的访问次数

    def get_rng(self, path: str) -> random.Random:
        """
        获取指定路径的 RNG 实例

        Args:
            path: 种子路径（如 "combat/round_1"）

        Returns:
            独立的 Random 实例

        Example:
            rng_instance = rng.get_rng("player/attack")
            # 可以直接使用 random.Random 的所有方法
            value = rng_instance.random()
        """
        if path not in self.rngs:
            # 组合种子：base_seed XOR hash(path)
            # 使用 XOR 而非加法，避免碰撞
            seed = self.base_seed ^ hash(path)
            self.rngs[path] = random.Random(seed)
            self._access_count[path] = 0

        self._access_count[path] += 1
        return self.rngs[path]

    def randint(self, path: str, a: int, b: int) -> int:
        """
        生成随机整数 [a, b]

        Args:
            path: 种子路径
            a: 最小值（包含）
            b: 最大值（包含）

        Returns:
            随机整数

        Example:
            dice_roll = rng.randint("combat/dice", 1, 20)
        """
        return self.get_rng(path).randint(a, b)

    def random(self, path: str) -> float:
        """
        生成随机浮点数 [0.0, 1.0)

        Args:
            path: 种子路径

        Returns:
            随机浮点数

        Example:
            probability = rng.random("event/trigger")
            if probability < 0.3:
                trigger_event()
        """
        return self.get_rng(path).random()

    def choice(self, path: str, seq: List[T]) -> T:
        """
        从序列中随机选择一个元素

        Args:
            path: 种子路径
            seq: 序列

        Returns:
            随机选择的元素

        Example:
            action = rng.choice("ai/action", ["attack", "defend", "flee"])
        """
        return self.get_rng(path).choice(seq)

    def shuffle(self, path: str, seq: List[T]) -> List[T]:
        """
        随机打乱序列（返回新列表，不修改原列表）

        Args:
            path: 种子路径
            seq: 原始序列

        Returns:
            打乱后的新列表

        Example:
            deck = ["A", "B", "C", "D"]
            shuffled = rng.shuffle("cards/deck", deck)
        """
        new_seq = seq.copy()
        self.get_rng(path).shuffle(new_seq)
        return new_seq

    def sample(self, path: str, population: List[T], k: int) -> List[T]:
        """
        从总体中随机抽取 k 个不重复的元素

        Args:
            path: 种子路径
            population: 总体
            k: 抽取数量

        Returns:
            随机抽取的元素列表

        Example:
            enemies = ["goblin", "orc", "troll", "dragon"]
            spawned = rng.sample("encounter/enemies", enemies, 2)
        """
        return self.get_rng(path).sample(population, k)

    def uniform(self, path: str, a: float, b: float) -> float:
        """
        生成均匀分布的随机浮点数 [a, b)

        Args:
            path: 种子路径
            a: 最小值
            b: 最大值

        Returns:
            随机浮点数

        Example:
            damage = rng.uniform("combat/damage", 10.0, 20.0)
        """
        return self.get_rng(path).uniform(a, b)

    def gauss(self, path: str, mu: float, sigma: float) -> float:
        """
        生成高斯分布的随机浮点数

        Args:
            path: 种子路径
            mu: 均值
            sigma: 标准差

        Returns:
            随机浮点数

        Example:
            # 生成接近 100 的随机值（标准差 15）
            stat = rng.gauss("character/stat", 100, 15)
        """
        return self.get_rng(path).gauss(mu, sigma)

    def get_stats(self) -> dict[str, Any]:
        """
        获取 RNG 使用统计

        Returns:
            统计信息字典

        Example:
            stats = rng.get_stats()
            print(f"Total paths used: {stats['total_paths']}")
        """
        return {
            "base_seed": self.base_seed,
            "total_paths": len(self.rngs),
            "access_counts": self._access_count.copy(),
            "most_used_path": max(
                self._access_count.items(),
                key=lambda x: x[1],
                default=("none", 0)
            )[0] if self._access_count else None
        }

    def reset_path(self, path: str) -> None:
        """
        重置指定路径的 RNG（用于测试）

        Args:
            path: 要重置的路径
        """
        if path in self.rngs:
            del self.rngs[path]
            del self._access_count[path]

    def clear_all(self) -> None:
        """
        清空所有 RNG 实例（用于测试）
        """
        self.rngs.clear()
        self._access_count.clear()

    def __repr__(self) -> str:
        return (
            f"SeededRNG(base_seed={self.base_seed}, "
            f"paths={len(self.rngs)}, "
            f"total_calls={sum(self._access_count.values())})"
        )
