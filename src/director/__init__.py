"""Global Director 模块

包含事件调度、一致性审计、线索经济管理等核心功能
"""

from .event_scoring import EventScorer, EventScore, ScoringMode
from .consistency_auditor import (
    ConsistencyAuditor,
    ConsistencyViolation,
    AuditReport,
    ViolationType,
    ViolationSeverity
)
from .clue_economy_manager import ClueEconomyManager, ClueHealthMetrics
from .global_director import GlobalDirector, DirectorConfig, DirectorMode, DirectorDecision

__all__ = [
    # 事件评分
    "EventScorer",
    "EventScore",
    "ScoringMode",
    # 一致性审计
    "ConsistencyAuditor",
    "ConsistencyViolation",
    "AuditReport",
    "ViolationType",
    "ViolationSeverity",
    # 线索经济
    "ClueEconomyManager",
    "ClueHealthMetrics",
    # 全局导演
    "GlobalDirector",
    "DirectorConfig",
    "DirectorMode",
    "DirectorDecision",
]
