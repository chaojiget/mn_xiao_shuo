"""
WorldClock 测试

测试时间推进、重置、步长设置等功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from src.sim.clock import WorldClock


class TestWorldClock:
    """WorldClock 测试类"""

    def test_initialization(self):
        """测试初始化"""
        clock = WorldClock(start=0, step=1)
        assert clock.get_time() == 0
        assert clock.step == 1
        assert clock.get_tick_count() == 0

    def test_tick(self):
        """测试时间推进"""
        clock = WorldClock(start=0, step=1)
        assert clock.tick() == 1
        assert clock.tick() == 2
        assert clock.tick() == 3
        assert clock.get_time() == 3
        assert clock.get_tick_count() == 3

    def test_custom_step(self):
        """测试自定义步长"""
        clock = WorldClock(start=10, step=5)
        assert clock.tick() == 15
        assert clock.tick() == 20
        assert clock.tick() == 25
        assert clock.get_time() == 25

    def test_reset(self):
        """测试重置"""
        clock = WorldClock(start=0, step=1)
        clock.tick()
        clock.tick()
        assert clock.get_time() == 2
        assert clock.get_tick_count() == 2

        clock.reset(0)
        assert clock.get_time() == 0
        assert clock.get_tick_count() == 0

    def test_reset_to_custom_time(self):
        """测试重置到自定义时间"""
        clock = WorldClock(start=0, step=1)
        clock.tick()
        clock.tick()

        clock.reset(100)
        assert clock.get_time() == 100
        assert clock.get_tick_count() == 0

        # 继续推进
        assert clock.tick() == 101

    def test_set_step(self):
        """测试设置步长"""
        clock = WorldClock(start=0, step=1)
        clock.tick()
        assert clock.get_time() == 1

        clock.set_step(10)
        clock.tick()
        assert clock.get_time() == 11

    def test_invalid_step(self):
        """测试无效步长"""
        clock = WorldClock()
        with pytest.raises(ValueError, match="Step must be positive"):
            clock.set_step(0)

        with pytest.raises(ValueError, match="Step must be positive"):
            clock.set_step(-1)

    def test_repr(self):
        """测试字符串表示"""
        clock = WorldClock(start=0, step=1)
        clock.tick()
        repr_str = repr(clock)
        assert "WorldClock" in repr_str
        assert "t=1" in repr_str
        assert "step=1" in repr_str
        assert "ticks=1" in repr_str


class TestWorldClockIntegration:
    """WorldClock 集成测试"""

    def test_long_run(self):
        """测试长时间运行"""
        clock = WorldClock(start=0, step=1)
        for _ in range(1000):
            clock.tick()

        assert clock.get_time() == 1000
        assert clock.get_tick_count() == 1000

    def test_variable_step(self):
        """测试可变步长"""
        clock = WorldClock(start=0, step=1)

        # 步长1：前10个tick
        for _ in range(10):
            clock.tick()
        assert clock.get_time() == 10

        # 步长5：接下来10个tick
        clock.set_step(5)
        for _ in range(10):
            clock.tick()
        assert clock.get_time() == 60  # 10 + 50

        # 步长1：最后10个tick
        clock.set_step(1)
        for _ in range(10):
            clock.tick()
        assert clock.get_time() == 70


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
