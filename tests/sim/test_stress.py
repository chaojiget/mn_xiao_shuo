"""
压力测试 - 验证 Simulation 在长时间运行下的性能和稳定性

测试目标：
- 1000+ ticks 长时间运行
- 内存使用稳定性
- 性能指标收集
- 大量事件和快照
"""

import sys
import pytest
import time
import psutil
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.sim.simulation import Simulation
from src.sim.event_store import Event
from src.models.world_state import WorldState, Character, Location, Faction, Resource


class TestLongRunSimulation:
    """长时间运行测试"""

    def test_run_1000_ticks(self):
        """测试运行 1000 ticks"""
        sim = Simulation(seed=42, setting={})

        start = time.time()
        sim.run(max_ticks=1000)
        elapsed = time.time() - start

        assert sim.get_current_tick() == 1000
        assert sim.event_store.count() > 0
        assert elapsed < 1.0  # 应该在 1 秒内完成

        print(f"\n  ✅ 1000 ticks 运行时间: {elapsed*1000:.2f}ms")

    def test_run_5000_ticks(self):
        """测试运行 5000 ticks"""
        sim = Simulation(seed=42, setting={})

        start = time.time()
        sim.run(max_ticks=5000)
        elapsed = time.time() - start

        assert sim.get_current_tick() == 5000
        assert sim.event_store.count() > 0
        assert elapsed < 5.0  # 应该在 5 秒内完成

        print(f"\n  ✅ 5000 ticks 运行时间: {elapsed*1000:.2f}ms")

    def test_run_10000_ticks(self):
        """测试运行 10000 ticks"""
        sim = Simulation(seed=42, setting={})

        start = time.time()
        sim.run(max_ticks=10000)
        elapsed = time.time() - start

        assert sim.get_current_tick() == 10000
        assert sim.event_store.count() > 0
        assert elapsed < 10.0  # 应该在 10 秒内完成

        print(f"\n  ✅ 10000 ticks 运行时间: {elapsed*1000:.2f}ms")


class TestMemoryUsage:
    """内存使用测试"""

    def test_memory_stability_1000_ticks(self):
        """测试 1000 ticks 内存稳定性"""
        process = psutil.Process()

        sim = Simulation(seed=42, setting={})

        # 记录初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 运行 1000 ticks
        sim.run(max_ticks=1000)

        # 记录最终内存
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        assert memory_increase < 50  # 内存增长应小于 50MB

        print(f"\n  初始内存: {initial_memory:.2f}MB")
        print(f"  最终内存: {final_memory:.2f}MB")
        print(f"  增长: {memory_increase:.2f}MB")

    def test_memory_with_world_state(self):
        """测试包含 WorldState 的内存使用"""
        process = psutil.Process()
        sim = Simulation(seed=42, setting={})

        # 添加大量实体到 WorldState
        for i in range(100):
            char = Character(
                id=f"char_{i}",
                name=f"Character {i}",
                role="neutral",
                description=f"Test character {i}",
                attributes={f"attr_{j}": float(j) for j in range(10)}
            )
            sim.world_state.characters[f"char_{i}"] = char

        for i in range(50):
            loc = Location(
                id=f"loc_{i}",
                name=f"Location {i}",
                type="area",
                description=f"Test location {i}",
                properties={f"prop_{j}": j for j in range(5)}
            )
            sim.world_state.locations[f"loc_{i}"] = loc

        initial_memory = process.memory_info().rss / 1024 / 1024

        # 运行模拟
        sim.run(max_ticks=1000)

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        assert memory_increase < 100  # 内存增长应小于 100MB

        print(f"\n  实体数: 100 角色 + 50 地点")
        print(f"  内存增长: {memory_increase:.2f}MB")


class TestSnapshotStress:
    """快照压力测试"""

    def test_multiple_snapshots_performance(self):
        """测试创建多个快照的性能"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=1000)

        # 创建 100 个快照
        start = time.time()
        snapshots = []
        for _ in range(100):
            snapshot = sim.snapshot()
            snapshots.append(snapshot)
        elapsed = time.time() - start

        assert len(snapshots) == 100
        assert elapsed < 1.0  # 100 个快照应在 1 秒内完成

        print(f"\n  ✅ 创建 100 个快照: {elapsed*1000:.2f}ms")
        print(f"  平均每个快照: {elapsed*1000/100:.2f}ms")

    def test_snapshot_restore_cycle(self):
        """测试快照-恢复循环"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=1000)

        # 多次快照-恢复循环
        start = time.time()
        for i in range(50):
            snapshot = sim.snapshot()
            sim.restore(snapshot)
        elapsed = time.time() - start

        assert sim.get_current_tick() == 1000
        assert elapsed < 2.0  # 50 次循环应在 2 秒内完成

        print(f"\n  ✅ 50 次快照-恢复循环: {elapsed*1000:.2f}ms")
        print(f"  平均每次循环: {elapsed*1000/50:.2f}ms")

    def test_large_world_state_snapshot(self):
        """测试大型 WorldState 快照"""
        sim = Simulation(seed=42, setting={})

        # 创建大型世界状态
        for i in range(500):
            char = Character(
                id=f"char_{i}",
                name=f"Character {i}",
                role="neutral",
                description="Test",
                attributes={f"attr_{j}": float(j) for j in range(20)},
                inventory=[f"item_{j}" for j in range(10)]
            )
            sim.world_state.characters[f"char_{i}"] = char

        # 测试快照性能
        start = time.time()
        snapshot = sim.snapshot()
        elapsed = time.time() - start

        assert snapshot.world_state is not None
        assert len(snapshot.world_state['characters']) == 500
        assert elapsed < 0.5  # 大型快照应在 0.5 秒内完成

        print(f"\n  实体数: 500 角色")
        print(f"  快照时间: {elapsed*1000:.2f}ms")


class TestReplayStress:
    """回放压力测试"""

    def test_replay_performance_1000_ticks(self):
        """测试回放到不同时间点的性能"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=1000)

        # 测试回放到不同时间点（默认事件只到 tick=100）
        targets = [100, 50, 80, 30, 90, 20, 70, 40]

        start = time.time()
        for target in targets:
            sim.replay(to_tick=target)
            assert sim.get_current_tick() == target
        elapsed = time.time() - start

        assert elapsed < 0.5  # 8 次回放应在 0.5 秒内完成

        print(f"\n  ✅ 8 次回放: {elapsed*1000:.2f}ms")
        print(f"  平均每次: {elapsed*1000/8:.2f}ms")

    def test_replay_with_world_state(self):
        """测试包含 WorldState 的回放"""
        sim = Simulation(seed=42, setting={})

        # 添加 WorldState 实体
        for i in range(100):
            char = Character(
                id=f"char_{i}",
                name=f"Character {i}",
                role="neutral",
                description="Test"
            )
            sim.world_state.characters[f"char_{i}"] = char

        sim.run(max_ticks=1000)

        # 测试回放性能（默认事件只到 tick=100）
        start = time.time()
        sim.replay(to_tick=50)
        elapsed = time.time() - start

        assert sim.get_current_tick() == 50
        assert len(sim.world_state.characters) == 100  # WorldState 保持不变
        assert elapsed < 0.1  # 应在 0.1 秒内完成

        print(f"\n  回放时间: {elapsed*1000:.2f}ms")


class TestEventStoreStress:
    """EventStore 压力测试"""

    def test_large_event_history(self):
        """测试大量事件历史"""
        sim = Simulation(seed=42, setting={})

        # 添加大量自定义事件
        for i in range(10000):
            event = Event(
                tick=i,
                actor=f"actor_{i % 100}",
                action="custom_action",
                payload={"data": f"event_{i}"},
                seed=f"{sim.seed}/{i}"
            )
            sim.append_event(event)

        assert sim.event_store.count() == 10000

        # 测试查询性能
        start = time.time()
        events = sim.event_store.get_events(from_tick=0, to_tick=5000)
        elapsed = time.time() - start

        assert len(events) == 5001  # 包含 0 到 5000
        assert elapsed < 0.1  # 查询应在 0.1 秒内完成

        print(f"\n  事件总数: {sim.event_store.count()}")
        print(f"  范围查询时间: {elapsed*1000:.2f}ms")


class TestDeterminismStress:
    """确定性压力测试"""

    def test_determinism_1000_ticks(self):
        """测试 1000 ticks 的确定性"""
        sim1 = Simulation(seed=42, setting={})
        sim2 = Simulation(seed=42, setting={})

        sim1.run(max_ticks=1000)
        sim2.run(max_ticks=1000)

        events1 = sim1.get_events()
        events2 = sim2.get_events()

        assert len(events1) == len(events2)

        for e1, e2 in zip(events1, events2):
            assert e1.tick == e2.tick
            assert e1.actor == e2.actor
            assert e1.action == e2.action

    def test_determinism_with_snapshots(self):
        """测试快照后的确定性"""
        sim1 = Simulation(seed=42, setting={})
        sim1.run(max_ticks=500)
        snap1 = sim1.snapshot()
        sim1.run(max_ticks=500)

        sim2 = Simulation(seed=42, setting={})
        sim2.run(max_ticks=500)
        snap2 = sim2.snapshot()
        sim2.run(max_ticks=500)

        # 快照应该相同
        assert snap1.tick == snap2.tick
        assert len(snap1.events) == len(snap2.events)


class TestPerformanceReport:
    """性能报告测试"""

    def test_comprehensive_performance(self):
        """综合性能测试"""
        print("\n")
        print("=" * 60)
        print("📊 综合性能测试报告")
        print("=" * 60)

        process = psutil.Process()

        # 1. 基础运行性能
        print("\n1️⃣ 基础运行性能")

        for ticks in [100, 500, 1000, 5000]:
            sim = Simulation(seed=42, setting={})  # 每次创建新实例
            start = time.time()
            sim.run(max_ticks=ticks)
            elapsed = time.time() - start

            events_per_sec = sim.event_store.count() / elapsed if elapsed > 0 else 0
            print(f"   {ticks:5d} ticks: {elapsed*1000:7.2f}ms ({events_per_sec:8.0f} events/s)")

        # 2. 快照性能
        print("\n2️⃣ 快照性能")
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=1000)

        start = time.time()
        snapshot = sim.snapshot()
        snap_time = time.time() - start

        start = time.time()
        sim.restore(snapshot)
        restore_time = time.time() - start

        print(f"   创建快照: {snap_time*1000:.2f}ms")
        print(f"   恢复快照: {restore_time*1000:.2f}ms")

        # 3. 回放性能
        print("\n3️⃣ 回放性能")
        # 使用同一个 sim（已经运行到 1000）
        # 注意：默认只有 10 个周期性事件（tick=10,20,...,100）
        # 所以只能回放到 <=100

        start = time.time()
        sim.replay(to_tick=50)
        replay_time = time.time() - start

        print(f"   回放到 tick=50: {replay_time*1000:.2f}ms")

        # 4. 内存使用
        print("\n4️⃣ 内存使用")
        memory = process.memory_info().rss / 1024 / 1024
        print(f"   当前内存: {memory:.2f}MB")

        # 5. WorldState 性能
        print("\n5️⃣ WorldState 性能")
        sim.reset()

        # 添加实体
        for i in range(200):
            char = Character(
                id=f"char_{i}",
                name=f"Character {i}",
                role="neutral",
                description="Test",
                attributes={f"attr_{j}": float(j) for j in range(10)}
            )
            sim.world_state.characters[f"char_{i}"] = char

        start = time.time()
        ws_dict = sim.world_state.to_dict()
        serialize_time = time.time() - start

        start = time.time()
        WorldState.from_dict(ws_dict)
        deserialize_time = time.time() - start

        print(f"   序列化 (200 角色): {serialize_time*1000:.2f}ms")
        print(f"   反序列化 (200 角色): {deserialize_time*1000:.2f}ms")

        print("\n" + "=" * 60)
        print("✅ 性能测试完成")
        print("=" * 60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
