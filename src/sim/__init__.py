"""
模拟器核心模块 (Simulation Core)

这个模块提供了沉浸式叙事模拟器的核心机制：
- WorldClock: 时间推进
- Scheduler: 事件调度
- EventStore: 事件溯源
- Simulation: 顶层协调器
"""

from .clock import WorldClock

# 以下模块将在后续 Day 实现后逐步启用
# from .scheduler import Scheduler, Task
# from .event_store import EventStore, Event
# from .simulation import Simulation, Snapshot, ReplayHandle

__all__ = [
    "WorldClock",
    # "Scheduler",
    # "Task",
    # "EventStore",
    # "Event",
    # "Simulation",
    # "Snapshot",
    # "ReplayHandle",
]
