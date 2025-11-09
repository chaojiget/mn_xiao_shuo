"""
Simulation - 模拟器

顶层协调器，集成 Clock + Scheduler + EventStore + GlobalDirector。
负责驱动整个模拟循环，管理时间推进、事件调度和状态同步。
"""

from typing import Dict, Any, Optional, Callable
from pathlib import Path

from .clock import WorldClock
from .scheduler import Scheduler, Task
from .event_store import EventStore, Event


class Simulation:
    """
    模拟器：协调 Clock + Scheduler + EventStore + GlobalDirector

    核心职责：
    1. 时间推进（Clock）
    2. 事件调度（Scheduler）
    3. 事件记录（EventStore）
    4. 业务逻辑协调（GlobalDirector，可选）

    特性：
    - 确定性运行（基于 seed）
    - 支持保存/加载
    - 支持快照/恢复
    - 支持回放
    """

    def __init__(
        self,
        seed: int,
        setting: Optional[Dict[str, Any]] = None,
        director: Optional[Any] = None  # GlobalDirector 实例（可选）
    ):
        """
        初始化模拟器

        Args:
            seed: 随机种子（用于确定性运行）
            setting: 世界设定（可选）
            director: GlobalDirector 实例（可选，Phase 2 集成）
        """
        self.seed = seed
        self.setting = setting or {}
        self.director = director

        # 核心组件
        self.clock = WorldClock()
        self.scheduler = Scheduler()
        self.event_store = EventStore()

        # 运行状态
        self._running = False
        self._max_ticks = 0

        # 初始化调度（示例）
        self._initialize_schedule()

    def _initialize_schedule(self) -> None:
        """
        初始化调度任务

        这是一个示例实现，实际项目中会根据世界设定动态调度。
        Phase 2 集成 GlobalDirector 后，这里会调用 director 的初始化逻辑。
        """
        # 示例：每 10 tick 触发一个周期性事件
        for i in range(1, 11):
            tick = i * 10
            self.scheduler.schedule(
                when=tick,
                fn=lambda t=tick: self._on_periodic_event(t),
                label=f"periodic_{tick}"
            )

    def _on_periodic_event(self, tick: int) -> None:
        """
        周期性事件处理（示例）

        Args:
            tick: 当前时间
        """
        event = Event(
            tick=tick,
            actor="system",
            action="periodic",
            payload={"message": f"Tick {tick}"},
            seed=f"{self.seed}/{tick}"
        )
        self.event_store.append(event)

    def run(self, max_ticks: int) -> None:
        """
        运行模拟

        Args:
            max_ticks: 最大运行 tick 数

        Example:
            sim = Simulation(seed=42, setting={})
            sim.run(max_ticks=100)
        """
        self._running = True
        self._max_ticks = max_ticks

        for _ in range(max_ticks):
            # 时钟推进
            tick = self.clock.tick()

            # 执行到期任务
            tasks = self.scheduler.pop_due(tick)
            for task in tasks:
                task.fn()

            # 如果有 GlobalDirector，调用其场景循环
            if self.director:
                # Phase 2: director.run_scene_loop(tick)
                pass

        self._running = False

    def get_events(self) -> list:
        """
        获取所有事件

        Returns:
            事件列表
        """
        return self.event_store.events

    def get_current_tick(self) -> int:
        """
        获取当前时间

        Returns:
            当前 tick
        """
        return self.clock.get_time()

    def is_running(self) -> bool:
        """
        检查是否正在运行

        Returns:
            运行状态
        """
        return self._running

    def save(self, path: Path) -> None:
        """
        保存模拟状态到文件

        Args:
            path: 文件路径

        Example:
            sim.save(Path("data/simulation.json"))
        """
        self.event_store.save_to_file(path)

    def load(self, path: Path) -> None:
        """
        从文件加载模拟状态

        Args:
            path: 文件路径

        Example:
            sim.load(Path("data/simulation.json"))
        """
        self.event_store.load_from_file(path)

    def reset(self) -> None:
        """
        重置模拟器到初始状态
        """
        self.clock.reset()
        self.scheduler.clear()
        self.event_store.clear()
        self._initialize_schedule()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取模拟器统计信息

        Returns:
            统计数据字典
        """
        return {
            "seed": self.seed,
            "current_tick": self.clock.get_time(),
            "total_ticks": self.clock.get_tick_count(),
            "event_count": self.event_store.count(),
            "pending_tasks": self.scheduler.size(),
            "running": self._running
        }

    def schedule_custom_task(
        self,
        when: int,
        fn: Callable,
        label: str = ""
    ) -> None:
        """
        调度自定义任务

        Args:
            when: 执行时间
            fn: 执行函数
            label: 任务标签

        Example:
            sim.schedule_custom_task(
                when=50,
                fn=lambda: print("Custom event"),
                label="custom_event"
            )
        """
        self.scheduler.schedule(when=when, fn=fn, label=label)

    def append_event(self, event: Event) -> None:
        """
        手动追加事件（用于外部集成）

        Args:
            event: 要追加的事件
        """
        self.event_store.append(event)

    def __repr__(self) -> str:
        return (
            f"Simulation(seed={self.seed}, "
            f"tick={self.clock.get_time()}, "
            f"events={self.event_store.count()}, "
            f"tasks={self.scheduler.size()})"
        )
