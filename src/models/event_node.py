"""事件节点与事件线数据模型"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class EventStatus(Enum):
    """事件状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class EventNode:
    """事件节点（故事的一个片段/场景）"""
    id: str
    arc_id: str  # 所属事件线
    title: str
    goal: str  # 本事件的目标

    # 前置条件
    prerequisites: List[str] = field(default_factory=list)  # event_ids
    required_flags: Dict[str, bool] = field(default_factory=dict)
    required_resources: Dict[str, float] = field(default_factory=dict)

    # 效果
    effects: Dict[str, Any] = field(default_factory=dict)  # 状态变化
    rewards: Dict[str, Any] = field(default_factory=dict)

    # 评分指标（用于GD调度）
    tension_delta: float = 0.0  # 张力增量

    # 可玩性指标
    puzzle_density: float = 0.0
    skill_checks_variety: float = 0.0
    failure_grace: float = 0.0  # 失败容错度
    hint_latency: float = 0.0
    exploit_resistance: float = 0.0
    reward_loop: float = 0.0

    # 叙事指标
    arc_progress: float = 0.0  # 对事件线推进的贡献
    theme_echo: float = 0.0  # 主题共鸣
    conflict_gradient: float = 0.0  # 冲突梯度
    payoff_debt: float = 0.0  # 偿还伏笔的程度
    scene_specificity: float = 0.0
    pacing_smoothness: float = 0.0

    # 玄幻专用指标
    upgrade_frequency: float = 0.0
    resource_gain: float = 0.0
    combat_variety: float = 0.0
    reversal_satisfaction: float = 0.0  # 逆袭爽感
    faction_expansion: float = 0.0

    # 线索经济
    setups: List[str] = field(default_factory=list)  # 埋下的伏笔IDs
    clues: List[str] = field(default_factory=list)  # 提供的线索IDs
    payoffs: List[str] = field(default_factory=list)  # 偿还的伏笔IDs

    # 状态
    status: EventStatus = EventStatus.PENDING
    attempts: int = 0  # 尝试次数（用于提示策略）

    # 元数据
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def is_available(self, world_state, completed_events: List[str]) -> bool:
        """检查事件是否可用"""
        # 检查前置事件
        for prereq in self.prerequisites:
            if prereq not in completed_events:
                return False

        # 检查标志位
        for flag, required_value in self.required_flags.items():
            if world_state.flags.get(flag) != required_value:
                return False

        # 检查资源
        for res_type, required_amount in self.required_resources.items():
            if res_type not in world_state.resources:
                return False
            if world_state.resources[res_type].amount < required_amount:
                return False

        return True


@dataclass
class EventArc:
    """事件线（一条故事线）"""
    id: str
    title: str
    description: str
    type: str  # main/side/hidden

    # 事件节点
    events: List[EventNode] = field(default_factory=list)

    # 进度
    current_event_idx: int = 0
    completed: bool = False

    # 主题
    themes: List[str] = field(default_factory=list)

    # 预计章节
    estimated_chapters: str = ""

    def get_next_event(self, world_state, completed_events: List[str]) -> Optional[EventNode]:
        """获取下一个可用事件"""
        for event in self.events:
            if event.status == EventStatus.PENDING and event.is_available(world_state, completed_events):
                return event
        return None

    def get_progress(self) -> float:
        """获取事件线进度(0.0-1.0)"""
        if not self.events:
            return 0.0
        completed = sum(1 for e in self.events if e.status == EventStatus.COMPLETED)
        return completed / len(self.events)
