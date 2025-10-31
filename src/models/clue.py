"""线索、伏笔、证据数据模型"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class ClueStatus(Enum):
    """线索状态"""
    HIDDEN = "hidden"  # 未发现
    DISCOVERED = "discovered"  # 已发现
    VERIFIED = "verified"  # 已验证
    MISLEADING = "misleading"  # 误导性


class SetupStatus(Enum):
    """伏笔状态"""
    PENDING = "pending"  # 待偿还
    HINTED = "hinted"  # 已暗示
    PAID_OFF = "paid_off"  # 已偿还
    OVERDUE = "overdue"  # 逾期


@dataclass
class Evidence:
    """证据（可验证的事实）"""
    id: str
    content: str
    type: str  # data/testimony/physical/document
    source: str  # 来源

    # 可信度
    credibility: float = 1.0  # 0.0-1.0

    # 关联
    related_clues: List[str] = field(default_factory=list)
    related_events: List[str] = field(default_factory=list)

    # 元数据
    discovered_at: Optional[datetime] = None
    location: Optional[str] = None


@dataclass
class Clue:
    """线索"""
    id: str
    content: str  # 线索内容
    type: str  # 类型（data_anomaly/witness/item等）

    # 证据链
    evidence_ids: List[str] = field(default_factory=list)
    verification_method: str = ""  # 如何验证

    # 状态
    status: ClueStatus = ClueStatus.HIDDEN

    # 关联
    related_event: Optional[str] = None  # 关联的事件
    leads_to: List[str] = field(default_factory=list)  # 指向的其他线索

    # 发现条件
    discovery_requirements: Dict[str, Any] = field(default_factory=dict)

    # 时间
    discovered_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None

    def verify(self, evidence: List[Evidence]) -> bool:
        """验证线索"""
        # 检查所有必需证据是否存在
        evidence_dict = {e.id: e for e in evidence}
        for eid in self.evidence_ids:
            if eid not in evidence_dict:
                return False

        # 这里可以添加更复杂的验证逻辑
        self.status = ClueStatus.VERIFIED
        self.verified_at = datetime.now()
        return True


@dataclass
class Setup:
    """伏笔（需要偿还的承诺）"""
    id: str
    description: str  # 伏笔描述
    setup_event_id: str  # 埋伏笔的事件

    # SLA (Service Level Agreement)
    sla_deadline: int  # 必须在多少回合内偿还
    setup_turn: int  # 埋下伏笔的回合

    # 偿还
    payoff_event_id: Optional[str] = None  # 偿还伏笔的事件
    payoff_turn: Optional[int] = None

    # 状态
    status: SetupStatus = SetupStatus.PENDING

    # 优先级
    priority: float = 1.0  # 越高越重要

    # 类型
    type: str = "plot"  # plot/character/world

    def is_overdue(self, current_turn: int) -> bool:
        """检查是否逾期"""
        if self.status == SetupStatus.PAID_OFF:
            return False
        return current_turn - self.setup_turn > self.sla_deadline

    def remaining_turns(self, current_turn: int) -> int:
        """剩余回合数"""
        if self.status == SetupStatus.PAID_OFF:
            return 0
        return max(0, self.sla_deadline - (current_turn - self.setup_turn))


@dataclass
class ClueRegistry:
    """线索注册表"""
    clues: Dict[str, Clue] = field(default_factory=dict)
    evidence: Dict[str, Evidence] = field(default_factory=dict)
    setups: Dict[str, Setup] = field(default_factory=dict)

    def add_clue(self, clue: Clue):
        """添加线索"""
        self.clues[clue.id] = clue

    def add_evidence(self, ev: Evidence):
        """添加证据"""
        self.evidence[ev.id] = ev

    def add_setup(self, setup: Setup):
        """添加伏笔"""
        self.setups[setup.id] = setup

    def get_overdue_setups(self, current_turn: int) -> List[Setup]:
        """获取逾期伏笔"""
        return [
            s for s in self.setups.values()
            if s.is_overdue(current_turn)
        ]

    def get_discovered_clues(self) -> List[Clue]:
        """获取已发现的线索"""
        return [
            c for c in self.clues.values()
            if c.status in [ClueStatus.DISCOVERED, ClueStatus.VERIFIED]
        ]
