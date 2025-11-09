"""
测试 Snapshot 快照机制

测试快照创建、恢复、多次快照等功能。
"""

import sys
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.sim.simulation import Simulation, Snapshot
from src.sim.event_store import Event


class TestSnapshot:
    """测试 Snapshot 数据类"""

    def test_snapshot_creation(self):
        """测试快照创建"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=30)

        # 创建快照
        snapshot = sim.snapshot()

        # 验证快照属性
        assert snapshot.tick == 30
        assert snapshot.clock_state["t"] == 30
        assert snapshot.clock_state["tick_count"] == 30
        assert len(snapshot.events) == 3  # tick 10, 20, 30

    def test_snapshot_contains_clock_state(self):
        """测试快照包含完整的时钟状态"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=25)

        snapshot = sim.snapshot()

        # 验证时钟状态
        assert "t" in snapshot.clock_state
        assert "step" in snapshot.clock_state
        assert "tick_count" in snapshot.clock_state

        assert snapshot.clock_state["t"] == 25
        assert snapshot.clock_state["step"] == 1
        assert snapshot.clock_state["tick_count"] == 25

    def test_snapshot_contains_scheduler_state(self):
        """测试快照包含调度器状态"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=15)

        snapshot = sim.snapshot()

        # 验证调度器状态（应该有剩余任务）
        assert isinstance(snapshot.scheduler_state, list)
        # 初始调度了 10, 20, 30, ..., 100
        # 已执行 10，剩余 20-100
        assert len(snapshot.scheduler_state) > 0

    def test_snapshot_contains_events(self):
        """测试快照包含事件历史"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=30)

        snapshot = sim.snapshot()

        # 验证事件列表
        assert isinstance(snapshot.events, list)
        assert len(snapshot.events) == 3
        assert all(isinstance(e, Event) for e in snapshot.events)

    def test_snapshot_deep_copy(self):
        """测试快照是深拷贝（修改原对象不影响快照）"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=30)

        snapshot = sim.snapshot()
        original_event_count = len(snapshot.events)

        # 继续运行模拟器
        sim.run(max_ticks=20)

        # 快照中的事件数量不应改变
        assert len(snapshot.events) == original_event_count
        assert len(sim.get_events()) > original_event_count

    def test_snapshot_metadata(self):
        """测试快照包含元数据"""
        setting = {"world_type": "scifi", "difficulty": "hard"}
        sim = Simulation(seed=42, setting=setting)
        sim.run(max_ticks=10)

        snapshot = sim.snapshot()

        # 验证元数据
        assert "metadata" in snapshot.__dict__
        assert snapshot.metadata["seed"] == 42
        assert snapshot.metadata["setting"] == setting

    def test_snapshot_repr(self):
        """测试快照的字符串表示"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=30)

        snapshot = sim.snapshot()
        snapshot_repr = repr(snapshot)

        assert "Snapshot" in snapshot_repr
        assert "tick=30" in snapshot_repr


class TestSnapshotRestore:
    """测试快照恢复功能"""

    def test_basic_restore(self):
        """测试基础的快照恢复"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=30)

        # 创建快照
        snapshot = sim.snapshot()
        assert snapshot.tick == 30

        # 继续运行
        sim.run(max_ticks=20)
        assert sim.get_current_tick() == 50

        # 恢复快照
        sim.restore(snapshot)

        # 验证状态恢复
        assert sim.get_current_tick() == 30
        assert sim.event_store.count() == 3

    def test_restore_clock_state(self):
        """测试恢复时钟状态"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=25)

        snapshot = sim.snapshot()

        # 继续运行
        sim.run(max_ticks=25)
        assert sim.clock.get_time() == 50
        assert sim.clock.get_tick_count() == 50

        # 恢复
        sim.restore(snapshot)

        # 验证时钟完全恢复
        assert sim.clock.get_time() == 25
        assert sim.clock.get_tick_count() == 25

    def test_restore_event_history(self):
        """测试恢复事件历史"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=30)

        snapshot = sim.snapshot()
        snapshot_events = len(snapshot.events)

        # 继续运行
        sim.run(max_ticks=30)
        assert sim.event_store.count() == 6

        # 恢复
        sim.restore(snapshot)

        # 验证事件历史恢复
        assert sim.event_store.count() == snapshot_events
        events = sim.get_events()
        assert [e.tick for e in events] == [10, 20, 30]

    def test_restore_and_continue(self):
        """测试恢复后继续运行"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=20)

        snapshot = sim.snapshot()

        # 继续运行
        sim.run(max_ticks=30)
        assert sim.get_current_tick() == 50

        # 恢复到 tick=20
        sim.restore(snapshot)
        assert sim.get_current_tick() == 20

        # 再次运行
        sim.run(max_ticks=10)
        assert sim.get_current_tick() == 30


class TestMultipleSnapshots:
    """测试多次快照"""

    def test_multiple_snapshots_at_different_times(self):
        """测试在不同时间点创建多个快照"""
        sim = Simulation(seed=42, setting={})

        snapshots = []

        # 每 10 ticks 创建一个快照
        for i in range(1, 6):
            sim.run(max_ticks=10)
            snapshot = sim.snapshot()
            snapshots.append(snapshot)

        # 验证快照时间点
        assert len(snapshots) == 5
        for i, snapshot in enumerate(snapshots):
            expected_tick = (i + 1) * 10
            assert snapshot.tick == expected_tick

    def test_restore_to_earlier_snapshot(self):
        """测试恢复到更早的快照"""
        sim = Simulation(seed=42, setting={})

        # 创建两个快照
        sim.run(max_ticks=20)
        snapshot1 = sim.snapshot()

        sim.run(max_ticks=20)
        snapshot2 = sim.snapshot()

        # 继续运行
        sim.run(max_ticks=20)
        assert sim.get_current_tick() == 60

        # 恢复到第二个快照
        sim.restore(snapshot2)
        assert sim.get_current_tick() == 40

        # 恢复到第一个快照
        sim.restore(snapshot1)
        assert sim.get_current_tick() == 20

    def test_snapshot_independence(self):
        """测试快照之间相互独立"""
        sim = Simulation(seed=42, setting={})

        sim.run(max_ticks=10)
        snapshot1 = sim.snapshot()

        sim.run(max_ticks=20)
        snapshot2 = sim.snapshot()

        # 修改模拟器状态
        sim.run(max_ticks=30)

        # 验证两个快照不受影响
        assert snapshot1.tick == 10
        assert len(snapshot1.events) == 1

        assert snapshot2.tick == 30
        assert len(snapshot2.events) == 3

    def test_many_snapshots(self):
        """测试大量快照（压力测试）"""
        sim = Simulation(seed=42, setting={})

        snapshots = []
        for i in range(20):
            sim.run(max_ticks=5)
            snapshot = sim.snapshot()
            snapshots.append(snapshot)

        # 验证所有快照
        assert len(snapshots) == 20
        for i, snapshot in enumerate(snapshots):
            expected_tick = (i + 1) * 5
            assert snapshot.tick == expected_tick


class TestSnapshotEdgeCases:
    """测试快照边界情况"""

    def test_snapshot_at_tick_zero(self):
        """测试在 tick=0 时创建快照"""
        sim = Simulation(seed=42, setting={})

        # 不运行，直接快照
        snapshot = sim.snapshot()

        assert snapshot.tick == 0
        assert len(snapshot.events) == 0

    def test_restore_to_tick_zero(self):
        """测试恢复到 tick=0"""
        sim = Simulation(seed=42, setting={})

        # 在 tick=0 创建快照
        snapshot_zero = sim.snapshot()

        # 运行一段时间
        sim.run(max_ticks=50)
        assert sim.get_current_tick() == 50

        # 恢复到 tick=0
        sim.restore(snapshot_zero)
        assert sim.get_current_tick() == 0
        assert sim.event_store.count() == 0

    def test_snapshot_after_reset(self):
        """测试重置后创建快照"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=30)

        # 重置
        sim.reset()

        # 创建快照
        snapshot = sim.snapshot()

        assert snapshot.tick == 0
        assert len(snapshot.events) == 0

    def test_restore_preserves_seed(self):
        """测试恢复后 seed 保持不变"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=20)

        snapshot = sim.snapshot()

        # 修改 seed（理论上不应该改变，但测试验证）
        sim.run(max_ticks=10)

        # 恢复
        sim.restore(snapshot)

        # seed 应该保持原值
        assert sim.seed == 42
        assert snapshot.metadata["seed"] == 42


class TestSnapshotIntegration:
    """集成测试：快照与其他功能的交互"""

    def test_snapshot_with_custom_tasks(self):
        """测试快照包含自定义任务"""
        sim = Simulation(seed=42, setting={})

        results = []

        # 添加自定义任务
        sim.schedule_custom_task(
            when=15,
            fn=lambda: results.append("task1"),
            label="custom1"
        )

        sim.run(max_ticks=10)
        snapshot = sim.snapshot()

        # 继续运行，执行自定义任务
        sim.run(max_ticks=10)
        assert "task1" in results

        # 恢复快照（任务会重新初始化）
        sim.restore(snapshot)
        assert sim.get_current_tick() == 10

    def test_snapshot_determinism(self):
        """测试快照的确定性"""
        # 创建两个相同 seed 的模拟器
        sim1 = Simulation(seed=42, setting={})
        sim2 = Simulation(seed=42, setting={})

        # 运行到相同时间点
        sim1.run(max_ticks=30)
        sim2.run(max_ticks=30)

        # 创建快照
        snapshot1 = sim1.snapshot()
        snapshot2 = sim2.snapshot()

        # 验证快照一致
        assert snapshot1.tick == snapshot2.tick
        assert len(snapshot1.events) == len(snapshot2.events)

        for e1, e2 in zip(snapshot1.events, snapshot2.events):
            assert e1.tick == e2.tick
            assert e1.actor == e2.actor
            assert e1.action == e2.action


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
