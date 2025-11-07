"""
Scheduler 测试

测试事件调度、优先级队列、部分弹出等功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from src.sim.scheduler import Scheduler, Task


class TestTask:
    """Task 测试类"""

    def test_task_creation(self):
        """测试任务创建"""
        task = Task(when=10, fn=lambda: None, label="test")
        assert task.when == 10
        assert task.label == "test"
        assert callable(task.fn)

    def test_task_comparison(self):
        """测试任务比较（基于时间）"""
        task1 = Task(when=5, fn=lambda: None)
        task2 = Task(when=10, fn=lambda: None)
        task3 = Task(when=5, fn=lambda: None)

        assert task1 < task2
        assert task2 > task1
        assert task1 == task3  # 相同时间视为相等

    def test_task_repr(self):
        """测试任务字符串表示"""
        task = Task(when=10, fn=lambda: None, label="greeting")
        repr_str = repr(task)
        assert "Task" in repr_str
        assert "when=10" in repr_str
        assert "greeting" in repr_str


class TestScheduler:
    """Scheduler 测试类"""

    def test_initialization(self):
        """测试初始化"""
        scheduler = Scheduler()
        assert scheduler.size() == 0
        assert scheduler.peek_next() is None

    def test_schedule_single_task(self):
        """测试调度单个任务"""
        scheduler = Scheduler()
        scheduler.schedule(when=10, fn=lambda: None, label="task1")

        assert scheduler.size() == 1
        next_task = scheduler.peek_next()
        assert next_task is not None
        assert next_task.when == 10
        assert next_task.label == "task1"

    def test_schedule_order(self):
        """测试调度顺序（按时间排序）"""
        scheduler = Scheduler()
        results = []

        # 乱序添加任务
        scheduler.schedule(when=5, fn=lambda: results.append("task1"), label="task1")
        scheduler.schedule(when=3, fn=lambda: results.append("task2"), label="task2")
        scheduler.schedule(when=7, fn=lambda: results.append("task3"), label="task3")
        scheduler.schedule(when=1, fn=lambda: results.append("task4"), label="task4")

        # 执行所有任务
        due = scheduler.pop_due(now=10)
        for task in due:
            task.fn()

        # 验证执行顺序
        assert results == ["task4", "task2", "task1", "task3"]

    def test_partial_pop(self):
        """测试部分弹出（只取到期任务）"""
        scheduler = Scheduler()
        scheduler.schedule(when=3, fn=lambda: None, label="task1")
        scheduler.schedule(when=5, fn=lambda: None, label="task2")
        scheduler.schedule(when=7, fn=lambda: None, label="task3")

        # 只弹出 tick <= 5 的任务
        due = scheduler.pop_due(now=5)
        assert len(due) == 2
        assert due[0].when == 3
        assert due[1].when == 5

        # 队列中还剩 1 个任务
        assert scheduler.size() == 1
        assert scheduler.peek_next().when == 7

        # 继续弹出
        due = scheduler.pop_due(now=10)
        assert len(due) == 1
        assert due[0].when == 7

        # 队列已空
        assert scheduler.size() == 0

    def test_peek_next(self):
        """测试查看下一个任务（不移除）"""
        scheduler = Scheduler()
        scheduler.schedule(when=5, fn=lambda: None)
        scheduler.schedule(when=3, fn=lambda: None)

        # peek 不移除任务
        next_task = scheduler.peek_next()
        assert next_task.when == 3
        assert scheduler.size() == 2  # 大小不变

        # 多次 peek 返回相同任务
        next_task2 = scheduler.peek_next()
        assert next_task2.when == 3

    def test_clear(self):
        """测试清空队列"""
        scheduler = Scheduler()
        scheduler.schedule(when=1, fn=lambda: None)
        scheduler.schedule(when=2, fn=lambda: None)
        scheduler.schedule(when=3, fn=lambda: None)

        assert scheduler.size() == 3

        scheduler.clear()
        assert scheduler.size() == 0
        assert scheduler.peek_next() is None

    def test_empty_pop(self):
        """测试空队列弹出"""
        scheduler = Scheduler()
        due = scheduler.pop_due(now=10)
        assert len(due) == 0

    def test_same_time_tasks(self):
        """测试相同时间的任务"""
        scheduler = Scheduler()
        results = []

        scheduler.schedule(when=5, fn=lambda: results.append("A"), label="A")
        scheduler.schedule(when=5, fn=lambda: results.append("B"), label="B")
        scheduler.schedule(when=5, fn=lambda: results.append("C"), label="C")

        due = scheduler.pop_due(now=5)
        assert len(due) == 3

        for task in due:
            task.fn()

        # 相同时间的任务都会被执行（顺序可能不固定）
        assert set(results) == {"A", "B", "C"}

    def test_get_all_tasks(self):
        """测试获取所有任务（不修改队列）"""
        scheduler = Scheduler()
        scheduler.schedule(when=5, fn=lambda: None, label="task1")
        scheduler.schedule(when=3, fn=lambda: None, label="task2")
        scheduler.schedule(when=7, fn=lambda: None, label="task3")

        all_tasks = scheduler.get_all_tasks()
        assert len(all_tasks) == 3
        assert [t.when for t in all_tasks] == [3, 5, 7]  # 按时间排序

        # 队列大小不变
        assert scheduler.size() == 3

    def test_repr(self):
        """测试字符串表示"""
        scheduler = Scheduler()
        repr_str = repr(scheduler)
        assert "Scheduler" in repr_str
        assert "empty" in repr_str

        scheduler.schedule(when=10, fn=lambda: None, label="test")
        repr_str = repr(scheduler)
        assert "size=1" in repr_str
        assert "next=10" in repr_str
        assert "test" in repr_str


class TestSchedulerIntegration:
    """Scheduler 集成测试"""

    def test_long_run(self):
        """测试长时间运行"""
        scheduler = Scheduler()
        results = []

        # 调度 100 个任务
        for i in range(100):
            scheduler.schedule(
                when=i * 10,
                fn=lambda idx=i: results.append(idx),
                label=f"task_{i}"
            )

        # 执行前 50 个任务（tick < 500）
        due = scheduler.pop_due(now=499)
        for task in due:
            task.fn()

        assert len(results) == 50
        assert results == list(range(50))

        # 执行剩余任务
        due = scheduler.pop_due(now=1000)
        for task in due:
            task.fn()

        assert len(results) == 100
        assert results == list(range(100))

    def test_dynamic_scheduling(self):
        """测试动态调度（执行中添加新任务）"""
        scheduler = Scheduler()
        results = []

        def task_with_spawn(label: str):
            """执行任务并调度新任务"""
            results.append(label)
            if label == "A":
                # A 执行时调度 D
                scheduler.schedule(when=15, fn=lambda: task_with_spawn("D"), label="D")

        scheduler.schedule(when=10, fn=lambda: task_with_spawn("A"), label="A")
        scheduler.schedule(when=20, fn=lambda: task_with_spawn("B"), label="B")
        scheduler.schedule(when=30, fn=lambda: task_with_spawn("C"), label="C")

        # 执行 tick=10 的任务
        due = scheduler.pop_due(now=10)
        for task in due:
            task.fn()
        assert results == ["A"]

        # 现在队列中有 B(20), C(30), D(15)
        assert scheduler.size() == 3

        # 执行 tick <= 20 的任务
        due = scheduler.pop_due(now=20)
        for task in due:
            task.fn()
        assert results == ["A", "D", "B"]  # D 在 B 之前

        # 执行剩余任务
        due = scheduler.pop_due(now=100)
        for task in due:
            task.fn()
        assert results == ["A", "D", "B", "C"]

    def test_with_clock(self):
        """测试与 WorldClock 集成"""
        from src.sim.clock import WorldClock

        clock = WorldClock(start=0, step=1)
        scheduler = Scheduler()
        results = []

        # 调度周期性任务
        for i in range(1, 11):
            tick = i * 10
            scheduler.schedule(
                when=tick,
                fn=lambda t=tick: results.append(t),
                label=f"periodic_{tick}"
            )

        # 模拟运行 100 ticks
        for _ in range(100):
            tick = clock.tick()
            due = scheduler.pop_due(now=tick)
            for task in due:
                task.fn()

        # 验证所有周期性任务都执行了
        assert results == [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
