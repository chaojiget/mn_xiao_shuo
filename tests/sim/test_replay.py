"""
测试 Replay 回放机制

测试回放功能、ReplayHandle 类等。
"""

import sys
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.sim.simulation import Simulation, ReplayHandle
from src.sim.event_store import Event


class TestReplay:
    """测试 Replay 回放功能"""

    def test_basic_replay(self):
        """测试基础回放"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=100)

        # 记录事件数
        events_at_100 = len(sim.get_events())
        assert events_at_100 == 10  # tick 10, 20, ..., 100

        # 回放到 tick=50
        sim.replay(to_tick=50)

        # 检查状态
        assert sim.get_current_tick() == 50
        assert len(sim.get_events()) == 5  # tick 10, 20, 30, 40, 50

    def test_replay_preserves_events(self):
        """测试回放保留事件历史"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=100)

        original_events = [e.tick for e in sim.get_events()]

        # 回放到 tick=50
        sim.replay(to_tick=50)

        replayed_events = [e.tick for e in sim.get_events()]

        # 应该保留 <= 50 的事件
        assert replayed_events == [10, 20, 30, 40, 50]
        assert all(tick in original_events for tick in replayed_events)

    def test_replay_to_zero(self):
        """测试回放到 tick=0"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=50)

        # 回放到 tick=0
        sim.replay(to_tick=0)

        assert sim.get_current_tick() == 0
        assert len(sim.get_events()) == 0

    def test_replay_and_continue(self):
        """测试回放后继续运行"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=100)

        # 回放到 tick=50
        sim.replay(to_tick=50)
        assert sim.get_current_tick() == 50

        # 继续运行到 tick=100
        sim.run(max_ticks=50)

        # 验证事件一致性
        assert sim.get_current_tick() == 100
        assert len(sim.get_events()) == 10

    def test_replay_multiple_times(self):
        """测试多次回放"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=100)

        # 第一次回放到 tick=30
        sim.replay(to_tick=30)
        assert sim.get_current_tick() == 30

        # 第二次回放到 tick=60
        sim.run(max_ticks=70)  # 先运行到 100
        sim.replay(to_tick=60)
        assert sim.get_current_tick() == 60

        # 第三次回放到 tick=10
        sim.replay(to_tick=10)
        assert sim.get_current_tick() == 10

    def test_replay_determinism(self):
        """测试回放的确定性"""
        sim1 = Simulation(seed=42, setting={})
        sim2 = Simulation(seed=42, setting={})

        # 两个模拟器都运行到 100
        sim1.run(max_ticks=100)
        sim2.run(max_ticks=100)

        # 回放到相同时间点
        sim1.replay(to_tick=50)
        sim2.replay(to_tick=50)

        # 验证状态一致
        events1 = [e.tick for e in sim1.get_events()]
        events2 = [e.tick for e in sim2.get_events()]

        assert events1 == events2
        assert sim1.get_current_tick() == sim2.get_current_tick()


class TestReplayEdgeCases:
    """测试回放边界情况"""

    def test_replay_invalid_negative_tick(self):
        """测试回放到负数 tick（应该失败）"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=50)

        with pytest.raises(ValueError, match="Invalid replay tick"):
            sim.replay(to_tick=-10)

    def test_replay_to_future_tick(self):
        """测试回放到未来 tick（应该失败）"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=50)

        with pytest.raises(ValueError, match="Cannot replay to future tick"):
            sim.replay(to_tick=100)

    def test_replay_to_current_tick(self):
        """测试回放到当前 tick"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=50)

        current_tick = sim.get_current_tick()

        # 回放到当前时间点
        sim.replay(to_tick=current_tick)

        assert sim.get_current_tick() == current_tick

    def test_replay_after_reset(self):
        """测试重置后回放"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=50)

        # 重置
        sim.reset()

        # 运行到新的时间点
        sim.run(max_ticks=30)

        # 回放到 tick=10
        sim.replay(to_tick=10)

        assert sim.get_current_tick() == 10


class TestReplayHandle:
    """测试 ReplayHandle 类"""

    def test_replay_handle_creation(self):
        """测试 ReplayHandle 创建"""
        sim = Simulation(seed=42, setting={})
        handle = sim.get_replay_handle()

        assert isinstance(handle, ReplayHandle)
        assert handle.simulation is sim

    def test_replay_handle_replay(self):
        """测试通过 ReplayHandle 回放"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=100)

        handle = sim.get_replay_handle()

        # 使用句柄回放
        handle.replay(to_tick=50)

        assert sim.get_current_tick() == 50
        assert handle.get_current_tick() == 50

    def test_replay_handle_snapshot(self):
        """测试通过 ReplayHandle 创建快照"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=50)

        handle = sim.get_replay_handle()

        # 创建快照
        snapshot = handle.snapshot()

        assert snapshot.tick == 50
        assert len(snapshot.events) == 5

    def test_replay_handle_restore(self):
        """测试通过 ReplayHandle 恢复快照"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=50)

        handle = sim.get_replay_handle()
        snapshot = handle.snapshot()

        # 继续运行
        sim.run(max_ticks=50)
        assert sim.get_current_tick() == 100

        # 使用句柄恢复
        handle.restore(snapshot)

        assert sim.get_current_tick() == 50
        assert handle.get_current_tick() == 50

    def test_replay_handle_get_events(self):
        """测试通过 ReplayHandle 获取事件"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=30)

        handle = sim.get_replay_handle()
        events = handle.get_events()

        assert len(events) == 3
        assert [e.tick for e in events] == [10, 20, 30]

    def test_replay_handle_workflow(self):
        """测试 ReplayHandle 完整工作流"""
        sim = Simulation(seed=42, setting={})
        handle = sim.get_replay_handle()

        # 运行到 tick=100
        sim.run(max_ticks=100)

        # 创建快照
        snapshot_100 = handle.snapshot()

        # 回放到 tick=50
        handle.replay(to_tick=50)
        assert handle.get_current_tick() == 50

        # 创建第二个快照
        snapshot_50 = handle.snapshot()

        # 恢复到 tick=100
        handle.restore(snapshot_100)
        assert handle.get_current_tick() == 100

        # 再次恢复到 tick=50
        handle.restore(snapshot_50)
        assert handle.get_current_tick() == 50

    def test_replay_handle_repr(self):
        """测试 ReplayHandle 字符串表示"""
        sim = Simulation(seed=42, setting={})
        handle = sim.get_replay_handle()

        handle_repr = repr(handle)
        assert "ReplayHandle" in handle_repr


class TestReplayIntegration:
    """集成测试：Replay 与其他功能的交互"""

    def test_replay_with_snapshot(self):
        """测试回放与快照的配合"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=100)

        # 创建快照
        snapshot = sim.snapshot()

        # 回放到 tick=50
        sim.replay(to_tick=50)

        # 恢复快照
        sim.restore(snapshot)

        # 验证恢复正确
        assert sim.get_current_tick() == 100
        assert len(sim.get_events()) == 10

    def test_replay_custom_events(self):
        """测试回放包含自定义事件"""
        sim = Simulation(seed=42, setting={})

        # 添加自定义事件
        sim.run(max_ticks=20)
        sim.append_event(Event(
            tick=25,
            actor="custom",
            action="custom_action",
            payload={"test": True},
            seed="custom/1"
        ))
        sim.run(max_ticks=30)  # 继续到 50

        # 回放到 tick=30
        sim.replay(to_tick=30)

        # 验证自定义事件被保留
        custom_events = [e for e in sim.get_events() if e.actor == "custom"]
        assert len(custom_events) == 1
        assert custom_events[0].tick == 25

    def test_replay_determinism_after_multiple_operations(self):
        """测试复杂操作后的回放确定性"""
        sim = Simulation(seed=42, setting={})

        # 运行到 tick=100
        sim.run(max_ticks=100)

        # 回放到 tick=30
        sim.replay(to_tick=30)
        assert sim.get_current_tick() == 30
        assert [e.tick for e in sim.get_events()] == [10, 20, 30]

        # 回放到 tick=60
        sim.replay(to_tick=60)
        assert sim.get_current_tick() == 60
        assert [e.tick for e in sim.get_events()] == [10, 20, 30, 40, 50, 60]

        # 回放到 tick=10
        sim.replay(to_tick=10)
        assert sim.get_current_tick() == 10
        assert [e.tick for e in sim.get_events()] == [10]

        # 回放到 tick=100
        sim.replay(to_tick=100)
        assert sim.get_current_tick() == 100
        assert len(sim.get_events()) == 10


class TestReplayPerformance:
    """测试回放性能"""

    def test_replay_long_run(self):
        """测试长时间运行后回放"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=1000)

        # 回放到 tick=100（初始调度器只支持到 tick=100）
        sim.replay(to_tick=100)

        assert sim.get_current_tick() == 100
        assert len(sim.get_events()) == 10  # 10, 20, ..., 100

        # 回放到 tick=50
        sim.replay(to_tick=50)
        assert sim.get_current_tick() == 50
        assert len(sim.get_events()) == 5  # 10, 20, 30, 40, 50

    def test_multiple_replays_performance(self):
        """测试多次回放的性能"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=100)

        # 记录原始最大 tick
        original_max_tick = max((e.tick for e in sim.get_events()), default=0)

        # 多次回放到不同时间点（只回放到已经运行过的时间）
        for target in [80, 60, 40, 20, 50, 70, 30]:
            sim.replay(to_tick=target)
            assert sim.get_current_tick() == target

            # 验证事件不超过目标时间
            events = sim.get_events()
            assert all(e.tick <= target for e in events)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
