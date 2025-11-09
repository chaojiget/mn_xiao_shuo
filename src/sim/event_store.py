"""
EventStore - 事件溯源

Append-only 事件日志，支持确定性回放和快照。
基于事件溯源模式，所有状态变更都通过事件记录。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path


@dataclass
class Event:
    """
    事件：不可变的事实记录

    事件是系统中发生的不可更改的事实。每个事件记录：
    - 发生时间（tick）
    - 执行者（actor）
    - 动作类型（action）
    - 动作数据（payload）
    - RNG 种子路径（seed）- 用于确定性回放
    """
    tick: int                   # 时间戳
    actor: str                  # 执行者（如 "player", "npc_001", "system"）
    action: str                 # 动作类型（如 "move", "attack", "talk"）
    payload: Dict[str, Any]     # 动作数据（如 {"to": "room1", "from": "room0"}）
    seed: str                   # RNG 种子路径（如 "seed/1/move"）

    def __repr__(self) -> str:
        return f"Event(t={self.tick}, actor='{self.actor}', action='{self.action}')"


class EventStore:
    """
    事件溯源存储：append-only 日志

    特性：
    - 只能追加，不能修改或删除已有事件
    - 支持按时间范围查询
    - 支持按执行者查询
    - 支持持久化到文件
    - 支持从文件加载
    """

    def __init__(self):
        self.events: List[Event] = []

    def append(self, event: Event) -> None:
        """
        追加事件（不可修改已有事件）

        Args:
            event: 要追加的事件

        Example:
            store.append(Event(
                tick=1,
                actor="player",
                action="move",
                payload={"to": "room1"},
                seed="seed/1"
            ))
        """
        self.events.append(event)

    def get_events(
        self,
        from_tick: int = 0,
        to_tick: Optional[int] = None
    ) -> List[Event]:
        """
        查询事件（按时间范围）

        Args:
            from_tick: 起始时间（包含）
            to_tick: 结束时间（包含），None 表示到最后

        Returns:
            事件列表

        Example:
            # 获取所有事件
            events = store.get_events()

            # 获取 tick 10 之后的事件
            events = store.get_events(from_tick=10)

            # 获取 tick 10-20 之间的事件
            events = store.get_events(from_tick=10, to_tick=20)
        """
        if to_tick is None:
            return [e for e in self.events if e.tick >= from_tick]
        return [
            e for e in self.events
            if from_tick <= e.tick <= to_tick
        ]

    def get_by_actor(self, actor: str) -> List[Event]:
        """
        查询特定执行者的事件

        Args:
            actor: 执行者名称

        Returns:
            该执行者的所有事件

        Example:
            player_events = store.get_by_actor("player")
        """
        return [e for e in self.events if e.actor == actor]

    def get_by_action(self, action: str) -> List[Event]:
        """
        查询特定动作类型的事件

        Args:
            action: 动作类型

        Returns:
            该动作类型的所有事件
        """
        return [e for e in self.events if e.action == action]

    def save_to_file(self, path: Path) -> None:
        """
        保存到文件

        Args:
            path: 文件路径

        Example:
            store.save_to_file(Path("data/events.json"))
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            data = [asdict(e) for e in self.events]
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_from_file(self, path: Path) -> None:
        """
        从文件加载

        Args:
            path: 文件路径

        Example:
            store.load_from_file(Path("data/events.json"))
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.events = [Event(**e) for e in data]

    def clear(self) -> None:
        """清空事件（仅测试用）"""
        self.events.clear()

    def count(self) -> int:
        """
        事件总数

        Returns:
            事件数量
        """
        return len(self.events)

    def get_last_event(self) -> Optional[Event]:
        """
        获取最后一个事件

        Returns:
            最后一个事件，如果为空则返回 None
        """
        return self.events[-1] if self.events else None

    def get_events_after(self, tick: int) -> List[Event]:
        """
        获取指定时间之后的事件（不包含指定时间）

        Args:
            tick: 时间点

        Returns:
            之后的所有事件
        """
        return [e for e in self.events if e.tick > tick]

    def __repr__(self) -> str:
        last_event = self.get_last_event()
        last_info = f"last={last_event.tick}@'{last_event.action}'" if last_event else "empty"
        return f"EventStore(count={self.count()}, {last_info})"
