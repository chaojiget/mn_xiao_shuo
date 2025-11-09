"""
Simulation - 模拟器

顶层协调器，集成 Clock + Scheduler + EventStore + GlobalDirector。
负责驱动整个模拟循环，管理时间推进、事件调度和状态同步。
"""

from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from dataclasses import dataclass, field
import copy

from .clock import WorldClock
from .scheduler import Scheduler, Task
from .event_store import EventStore, Event
from ..models.world_state import WorldState


@dataclass
class Snapshot:
    """
    模拟器快照：捕获特定时间点的完整状态

    快照包含：
    - 时间点（tick）
    - 时钟状态（当前时间、步长、tick计数）
    - 调度器状态（待执行任务队列）
    - 事件历史（所有已发生事件）
    - 世界状态（预留，Phase 2 集成 WorldState）

    快照用于：
    - 保存游戏进度
    - 实现"悔棋"功能
    - 回放到任意时间点
    - 调试和测试
    """
    tick: int                                   # 快照时间点
    clock_state: Dict[str, Any]                 # 时钟状态
    scheduler_state: List[Dict[str, Any]]       # 调度器任务列表
    events: List[Event]                         # 事件历史（深拷贝）
    world_state: Optional[Dict[str, Any]] = None  # 世界状态（预留）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据

    def __repr__(self) -> str:
        return (
            f"Snapshot(tick={self.tick}, "
            f"events={len(self.events)}, "
            f"tasks={len(self.scheduler_state)})"
        )


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
        self.world_state = WorldState(timestamp=0, turn=0)  # 世界状态

        # 运行状态
        self._running = False
        self._max_ticks = 0

        # 回放支持：保留完整事件历史（用于回放）
        self._full_event_history: List[Event] = []

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
        # 同时保存到完整历史（用于回放）
        self._full_event_history.append(event)

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
        self._full_event_history.clear()
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
        # 同时保存到完整历史
        self._full_event_history.append(event)

    def snapshot(self) -> Snapshot:
        """
        创建当前状态的快照

        快照捕获：
        - 时钟状态（时间、步长、tick计数）
        - 调度器状态（待执行任务）
        - 事件历史（深拷贝）
        - 世界状态（预留）

        Returns:
            Snapshot 对象

        Example:
            sim = Simulation(seed=42, setting={})
            sim.run(max_ticks=30)

            # 创建快照
            snapshot = sim.snapshot()

            # 继续运行
            sim.run(max_ticks=20)

            # 稍后恢复
            sim.restore(snapshot)
        """
        return Snapshot(
            tick=self.clock.get_time(),
            clock_state=self._get_clock_state(),
            scheduler_state=self._get_scheduler_state(),
            events=copy.deepcopy(self.event_store.events),
            world_state=self._get_world_state(),
            metadata={
                "seed": self.seed,
                "setting": self.setting
            }
        )

    def restore(self, snapshot: Snapshot) -> None:
        """
        从快照恢复状态

        恢复：
        - 时钟状态
        - 调度器状态（注意：需要重新创建任务函数）
        - 事件历史
        - 世界状态（预留）

        Args:
            snapshot: 要恢复的快照

        Example:
            sim.restore(snapshot)
            assert sim.get_current_tick() == snapshot.tick

        Note:
            由于 Snapshot 中保存的调度器任务不包含函数对象，
            恢复后需要重新初始化调度器。
            这在 Day 7 实现 Replay 机制时会完善。
        """
        # 恢复时钟
        self._restore_clock_state(snapshot.clock_state)

        # 恢复事件历史
        self.event_store.events = copy.deepcopy(snapshot.events)

        # 恢复调度器（暂时清空后重新初始化）
        # Phase 2: 实现更完善的任务序列化和恢复
        self.scheduler.clear()
        self._initialize_schedule()

        # 恢复世界状态（预留）
        if snapshot.world_state:
            self._restore_world_state(snapshot.world_state)

    def _get_clock_state(self) -> Dict[str, Any]:
        """获取时钟状态（深拷贝）"""
        return {
            "t": self.clock.t,
            "step": self.clock.step,
            "tick_count": self.clock._tick_count
        }

    def _restore_clock_state(self, state: Dict[str, Any]) -> None:
        """恢复时钟状态"""
        self.clock.t = state["t"]
        self.clock.step = state["step"]
        self.clock._tick_count = state["tick_count"]

    def _get_scheduler_state(self) -> List[Dict[str, Any]]:
        """
        获取调度器状态

        Note:
            由于 Task 包含函数对象（不可序列化），
            这里只保存任务的元数据（when, label）。
            实际应用中需要配合 Replay 机制重建任务。
        """
        tasks = self.scheduler.get_all_tasks()
        return [
            {
                "when": task.when,
                "label": task.label
            }
            for task in tasks
        ]

    def _get_world_state(self) -> Optional[Dict[str, Any]]:
        """
        获取世界状态（深拷贝）

        Returns:
            世界状态的字典表示，用于快照
        """
        return self.world_state.to_dict()

    def _restore_world_state(self, state: Dict[str, Any]) -> None:
        """
        恢复世界状态

        Args:
            state: 世界状态的字典表示

        Note:
            从快照恢复世界状态，重建所有角色、地点、势力等
        """
        self.world_state = WorldState.from_dict(state)

    def replay(self, to_tick: int) -> None:
        """
        回放到指定时间点

        通过基于完整事件历史恢复状态到目标时间点。
        使用内部保存的完整事件历史，允许前后跳转。

        Args:
            to_tick: 目标时间点

        Example:
            sim = Simulation(seed=42, setting={})
            sim.run(max_ticks=100)

            # 回放到 tick=50
            sim.replay(to_tick=50)
            assert sim.get_current_tick() == 50

            # 可以再回放到 tick=80
            sim.replay(to_tick=80)
            assert sim.get_current_tick() == 80

        Note:
            - 使用完整事件历史，支持前后跳转
            - 回放保留 <= to_tick 的事件
            - 调度器重新初始化
            - 时钟调整到目标时间点
        """
        if to_tick < 0:
            raise ValueError(f"Invalid replay tick: {to_tick} (must be >= 0)")

        # 使用完整事件历史检查
        full_max_tick = max((e.tick for e in self._full_event_history), default=0)

        if to_tick > full_max_tick and to_tick > 0:
            # 如果目标时间点超过完整历史，需要先运行到该时间点
            raise ValueError(
                f"Cannot replay to future tick {to_tick} "
                f"(max historical tick: {full_max_tick})"
            )

        # 从完整历史中过滤出目标时间点之前的事件
        target_events = [e for e in self._full_event_history if e.tick <= to_tick]

        # 重置状态
        self.clock.reset(0)
        self.scheduler.clear()
        self._initialize_schedule()
        self.event_store.clear()

        # 恢复事件（注意：不添加到完整历史，因为已经存在）
        for event in target_events:
            self.event_store.append(event)

        # 将时钟直接调整到目标时间点
        # 通过逐步 tick 推进，以便正确更新 tick_count
        while self.clock.get_time() < to_tick:
            self.clock.tick()
            # 清除已执行的任务（但不执行它们）
            self.scheduler.pop_due(self.clock.get_time())

    def get_replay_handle(self) -> 'ReplayHandle':
        """
        获取回放句柄

        返回一个 ReplayHandle 对象，提供回放、快照、恢复的统一接口。

        Returns:
            ReplayHandle 实例

        Example:
            sim = Simulation(seed=42, setting={})
            handle = sim.get_replay_handle()

            # 使用句柄操作
            handle.replay(to_tick=50)
            snapshot = handle.snapshot()
            handle.restore(snapshot)
        """
        return ReplayHandle(self)

    def __repr__(self) -> str:
        return (
            f"Simulation(seed={self.seed}, "
            f"tick={self.clock.get_time()}, "
            f"events={self.event_store.count()}, "
            f"tasks={self.scheduler.size()})"
        )


class ReplayHandle:
    """
    回放句柄：提供回放、快照、恢复的统一接口

    ReplayHandle 是 Simulation 的轻量级包装器，
    提供更清晰的 API 用于时间旅行操作。

    特性：
    - 回放到任意时间点
    - 创建和恢复快照
    - 统一的接口设计

    Example:
        sim = Simulation(seed=42, setting={})
        sim.run(max_ticks=100)

        # 获取回放句柄
        handle = sim.get_replay_handle()

        # 回放到 tick=50
        handle.replay(to_tick=50)

        # 创建快照
        snapshot = handle.snapshot()

        # 继续运行
        sim.run(max_ticks=30)

        # 恢复快照
        handle.restore(snapshot)
    """

    def __init__(self, simulation: 'Simulation'):
        """
        初始化回放句柄

        Args:
            simulation: Simulation 实例
        """
        self.simulation = simulation

    def replay(self, to_tick: int) -> None:
        """
        回放到指定时间点

        Args:
            to_tick: 目标时间点
        """
        self.simulation.replay(to_tick)

    def snapshot(self) -> Snapshot:
        """
        创建当前状态的快照

        Returns:
            Snapshot 对象
        """
        return self.simulation.snapshot()

    def restore(self, snapshot: Snapshot) -> None:
        """
        从快照恢复状态

        Args:
            snapshot: 要恢复的快照
        """
        self.simulation.restore(snapshot)

    def get_current_tick(self) -> int:
        """
        获取当前时间

        Returns:
            当前 tick
        """
        return self.simulation.get_current_tick()

    def get_events(self) -> list:
        """
        获取所有事件

        Returns:
            事件列表
        """
        return self.simulation.get_events()

    def __repr__(self) -> str:
        return f"ReplayHandle(simulation={self.simulation})"
