"""
测试 Simulation 模拟器

测试核心运行循环、确定性、保存/加载等功能。
"""

import sys
import tempfile
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.sim.simulation import Simulation
from src.sim.event_store import Event


class TestSimulation:
    """测试 Simulation 类"""

    def test_initialization(self):
        """测试初始化"""
        sim = Simulation(seed=42, setting={})

        assert sim.seed == 42
        assert sim.setting == {}
        assert sim.director is None
        assert sim.get_current_tick() == 0
        assert not sim.is_running()

    def test_basic_run(self):
        """测试基础运行"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=50)

        # 检查时钟推进
        assert sim.get_current_tick() == 50

        # 检查事件生成（周期性事件：10, 20, 30, 40, 50）
        events = sim.get_events()
        assert len(events) == 5

        # 验证事件时间点
        event_ticks = [e.tick for e in events]
        assert event_ticks == [10, 20, 30, 40, 50]

        # 验证不再运行
        assert not sim.is_running()

    def test_running_state(self):
        """测试运行状态标志"""
        sim = Simulation(seed=42, setting={})

        assert not sim.is_running()

        # 模拟运行过程（通过自定义任务验证）
        result = {"running_during": False}

        def check_running():
            result["running_during"] = sim.is_running()

        sim.schedule_custom_task(when=5, fn=check_running, label="check")
        sim.run(max_ticks=10)

        # 运行中应该是 True
        assert result["running_during"] is True
        # 运行后应该是 False
        assert not sim.is_running()

    def test_deterministic_run(self):
        """测试确定性运行（同 seed 相同结果）"""
        sim1 = Simulation(seed=42, setting={})
        sim2 = Simulation(seed=42, setting={})

        sim1.run(max_ticks=50)
        sim2.run(max_ticks=50)

        events1 = sim1.get_events()
        events2 = sim2.get_events()

        # 事件数量应该相同
        assert len(events1) == len(events2)

        # 每个事件的 tick 和 action 应该相同
        for e1, e2 in zip(events1, events2):
            assert e1.tick == e2.tick
            assert e1.actor == e2.actor
            assert e1.action == e2.action
            assert e1.payload == e2.payload

    def test_different_seeds(self):
        """测试不同 seed 产生不同随机序列（准备工作）"""
        sim1 = Simulation(seed=42, setting={})
        sim2 = Simulation(seed=43, setting={})

        sim1.run(max_ticks=50)
        sim2.run(max_ticks=50)

        # 周期性事件是确定的，所以这里只验证基础功能
        # Phase 2 集成 RNG 后会有真正的随机性差异
        events1 = sim1.get_events()
        events2 = sim2.get_events()

        assert len(events1) == len(events2)  # 目前周期事件数量相同

    def test_custom_task_scheduling(self):
        """测试自定义任务调度"""
        sim = Simulation(seed=42, setting={})
        results = []

        # 调度自定义任务
        sim.schedule_custom_task(
            when=15,
            fn=lambda: results.append("task1"),
            label="custom1"
        )
        sim.schedule_custom_task(
            when=25,
            fn=lambda: results.append("task2"),
            label="custom2"
        )

        sim.run(max_ticks=30)

        # 验证任务执行
        assert results == ["task1", "task2"]

    def test_manual_event_append(self):
        """测试手动追加事件"""
        sim = Simulation(seed=42, setting={})

        # 手动添加事件
        sim.append_event(Event(
            tick=5,
            actor="manual",
            action="test",
            payload={"data": "manual_event"},
            seed="manual/1"
        ))

        events = sim.get_events()
        assert len(events) == 1
        assert events[0].actor == "manual"

    def test_reset(self):
        """测试重置功能"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=50)

        assert sim.get_current_tick() == 50
        assert sim.event_store.count() == 5

        # 重置
        sim.reset()

        # 验证状态被重置
        assert sim.get_current_tick() == 0
        assert sim.event_store.count() == 0
        # 调度器应该重新初始化（包含新的周期任务）
        assert sim.scheduler.size() == 10

    def test_stats(self):
        """测试统计信息"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=30)

        stats = sim.get_stats()

        assert stats["seed"] == 42
        assert stats["current_tick"] == 30
        assert stats["total_ticks"] == 30
        assert stats["event_count"] == 3  # tick 10, 20, 30
        assert stats["running"] is False

    def test_persistence(self):
        """测试保存和加载"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=30)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "simulation.json"

            # 保存
            sim.save(path)
            assert path.exists()

            # 创建新模拟器并加载
            sim2 = Simulation(seed=99, setting={})  # 不同的 seed
            sim2.load(path)

            # 验证事件被正确加载
            assert sim2.event_store.count() == 3
            events = sim2.get_events()
            assert events[0].tick == 10
            assert events[1].tick == 20
            assert events[2].tick == 30

    def test_long_run(self):
        """测试长时间运行（100 ticks）"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=100)

        assert sim.get_current_tick() == 100
        assert sim.event_store.count() == 10  # 10, 20, ..., 100
        assert not sim.is_running()

    def test_repr(self):
        """测试字符串表示"""
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=20)

        sim_repr = repr(sim)
        assert "seed=42" in sim_repr
        assert "tick=20" in sim_repr
        assert "events=2" in sim_repr

    def test_multiple_runs(self):
        """测试多次运行"""
        sim = Simulation(seed=42, setting={})

        # 第一次运行
        sim.run(max_ticks=20)
        assert sim.get_current_tick() == 20
        events_after_first = len(sim.get_events())

        # 第二次运行（继续）
        sim.run(max_ticks=30)
        assert sim.get_current_tick() == 50
        events_after_second = len(sim.get_events())

        # 验证事件累积
        assert events_after_second > events_after_first

    def test_setting_parameter(self):
        """测试世界设定参数"""
        setting = {
            "world_type": "scifi",
            "difficulty": "hard",
            "features": ["combat", "exploration"]
        }

        sim = Simulation(seed=42, setting=setting)

        assert sim.setting == setting
        assert sim.setting["world_type"] == "scifi"

    def test_director_parameter(self):
        """测试 GlobalDirector 参数（预留）"""
        # 创建一个模拟的 director 对象
        class MockDirector:
            def __init__(self):
                self.called = False

        director = MockDirector()
        sim = Simulation(seed=42, setting={}, director=director)

        assert sim.director is director
        # Phase 2 会实际调用 director 的方法


class TestSimulationIntegration:
    """集成测试：验证多个组件协作"""

    def test_clock_scheduler_eventstore_integration(self):
        """测试 Clock + Scheduler + EventStore 集成"""
        sim = Simulation(seed=42, setting={})

        # 添加自定义任务，该任务会记录事件
        def record_custom_event():
            event = Event(
                tick=sim.get_current_tick(),
                actor="custom",
                action="custom_action",
                payload={"test": True},
                seed=f"custom/{sim.get_current_tick()}"
            )
            sim.append_event(event)

        sim.schedule_custom_task(when=15, fn=record_custom_event, label="custom")
        sim.run(max_ticks=50)

        # 验证自定义事件被记录
        custom_events = [e for e in sim.get_events() if e.actor == "custom"]
        assert len(custom_events) == 1
        assert custom_events[0].tick == 15

    def test_determinism_with_multiple_tasks(self):
        """测试多任务确定性"""
        def create_sim_with_tasks():
            sim = Simulation(seed=42, setting={})

            # 添加多个自定义任务
            for i in range(5):
                tick = (i + 1) * 7
                sim.schedule_custom_task(
                    when=tick,
                    fn=lambda t=tick: sim.append_event(Event(
                        tick=t,
                        actor="multi",
                        action=f"action_{t}",
                        payload={},
                        seed=f"multi/{t}"
                    )),
                    label=f"multi_{tick}"
                )

            sim.run(max_ticks=50)
            return sim

        sim1 = create_sim_with_tasks()
        sim2 = create_sim_with_tasks()

        # 验证完全一致
        events1 = sim1.get_events()
        events2 = sim2.get_events()

        assert len(events1) == len(events2)

        for e1, e2 in zip(events1, events2):
            assert e1.tick == e2.tick
            assert e1.actor == e2.actor
            assert e1.action == e2.action


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
