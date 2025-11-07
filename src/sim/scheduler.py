"""
Scheduler - 事件调度器

基于优先队列的任务调度系统，支持按时间顺序调度任务。
使用 heapq 实现最小堆，保证 O(log n) 的插入和弹出效率。
"""

import heapq
from typing import Callable, List, Optional
from dataclasses import dataclass, field


@dataclass(order=True)
class Task:
    """
    调度任务

    使用 @dataclass(order=True) 自动实现基于 when 的比较。
    compare=False 的字段不参与比较，避免函数对象比较错误。
    """
    when: int  # 执行时间（tick）
    fn: Callable = field(compare=False)  # 执行函数
    label: str = field(default="", compare=False)  # 任务标签（用于调试）

    def __repr__(self) -> str:
        return f"Task(when={self.when}, label='{self.label}')"


class Scheduler:
    """
    事件调度器：优先队列管理

    使用最小堆实现，保证任务按时间顺序执行。
    """

    def __init__(self):
        self.queue: List[Task] = []

    def schedule(self, when: int, fn: Callable, label: str = "") -> None:
        """
        调度任务到指定时间

        Args:
            when: 执行时间（tick）
            fn: 执行函数（无参数）
            label: 任务标签（可选，用于调试）

        Example:
            scheduler.schedule(when=10, fn=lambda: print("Hello"), label="greeting")
        """
        task = Task(when=when, fn=fn, label=label)
        heapq.heappush(self.queue, task)

    def pop_due(self, now: int) -> List[Task]:
        """
        获取所有到期任务

        Args:
            now: 当前时间（tick）

        Returns:
            所有到期任务列表（按时间排序）

        Example:
            tasks = scheduler.pop_due(now=15)
            for task in tasks:
                task.fn()
        """
        due = []
        while self.queue and self.queue[0].when <= now:
            due.append(heapq.heappop(self.queue))
        return due

    def peek_next(self) -> Optional[Task]:
        """
        查看下一个任务（不移除）

        Returns:
            下一个任务，如果队列为空则返回 None

        Example:
            next_task = scheduler.peek_next()
            if next_task:
                print(f"Next task at tick {next_task.when}")
        """
        return self.queue[0] if self.queue else None

    def clear(self) -> None:
        """清空队列"""
        self.queue.clear()

    def size(self) -> int:
        """
        队列大小

        Returns:
            队列中任务数量
        """
        return len(self.queue)

    def get_all_tasks(self) -> List[Task]:
        """
        获取所有任务（不修改队列）

        Returns:
            所有任务的副本（按时间排序）
        """
        return sorted(self.queue.copy(), key=lambda t: t.when)

    def __repr__(self) -> str:
        next_task = self.peek_next()
        next_info = f"next={next_task.when}@'{next_task.label}'" if next_task else "empty"
        return f"Scheduler(size={self.size()}, {next_info})"
