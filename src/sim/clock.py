"""
WorldClock - 世界时钟

提供时间推进机制，支持固定步长和可变步长。
所有模拟事件都基于时钟的 tick 进行调度。
"""

from typing import Optional


class WorldClock:
    """世界时钟：驱动模拟循环的时间系统"""

    def __init__(self, start: int = 0, step: int = 1):
        """
        初始化世界时钟

        Args:
            start: 起始时间（tick）
            step: 每次 tick 的步长
        """
        self.t: int = start
        self.step: int = step
        self._tick_count: int = 0  # 记录 tick 调用次数

    def tick(self) -> int:
        """
        推进一个时间步

        Returns:
            当前时间（tick 后）
        """
        self.t += self.step
        self._tick_count += 1
        return self.t

    def reset(self, start: int = 0) -> None:
        """
        重置时钟到指定时间

        Args:
            start: 重置后的起始时间
        """
        self.t = start
        self._tick_count = 0

    def get_time(self) -> int:
        """
        获取当前时间

        Returns:
            当前时间（tick）
        """
        return self.t

    def get_tick_count(self) -> int:
        """
        获取 tick 调用总次数

        Returns:
            tick 调用次数
        """
        return self._tick_count

    def set_step(self, step: int) -> None:
        """
        设置时间步长

        Args:
            step: 新的步长
        """
        if step <= 0:
            raise ValueError("Step must be positive")
        self.step = step

    def __repr__(self) -> str:
        return f"WorldClock(t={self.t}, step={self.step}, ticks={self._tick_count})"
