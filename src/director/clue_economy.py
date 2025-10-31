"""
线索经济管理系统
Clue Economy Management System

功能:
1. 线索注册与发现管理
2. 伏笔债务(Setup Debt)与SLA检查
3. 红鲱鱼(Red Herring)管理
4. 证据链验证
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
from datetime import datetime, timedelta
from uuid import uuid4


# ============================================================================
# 线索相关模型(扩展自 src/models/clue.py)
# ============================================================================

class ClueInstance(BaseModel):
    """线索实例"""
    clue_id: str = Field(default_factory=lambda: str(uuid4()))
    clue_type: Literal["implicit", "explicit", "red_herring"]

    # 线索内容
    content: str
    related_secret: Optional[str] = None  # 关联的秘密/真相

    # 发现状态
    discovered: bool = False
    discovered_at: Optional[datetime] = None
    discovered_by: str = "protagonist"

    # 验证方法
    verification_method: Optional[str] = None
    verified: bool = False

    # 可靠性(0-1, 红鲱鱼为低值)
    reliability: float = 1.0


class SetupDebt(BaseModel):
    """伏笔债务"""
    setup_id: str = Field(default_factory=lambda: str(uuid4()))

    # 伏笔内容
    description: str
    setup_type: Literal["foreshadowing", "promise", "mystery", "question"]

    # SLA (Service Level Agreement)
    created_at: datetime = Field(default_factory=datetime.now)
    deadline_turns: int = 20  # 必须在N回合内兑现
    current_turn: int = 0

    # 兑现状态
    paid_off: bool = False
    paid_off_at: Optional[datetime] = None
    payoff_event_id: Optional[str] = None

    # 优先级
    priority: Literal["low", "medium", "high", "critical"] = "medium"

    @property
    def is_overdue(self) -> bool:
        """是否已逾期"""
        return not self.paid_off and self.current_turn >= self.deadline_turns

    @property
    def urgency(self) -> float:
        """紧迫度(0-1)"""
        if self.paid_off:
            return 0.0
        progress = self.current_turn / self.deadline_turns
        return min(1.0, progress)

    def tick(self):
        """回合推进"""
        if not self.paid_off:
            self.current_turn += 1

    def pay_off(self, event_id: str):
        """兑现伏笔"""
        self.paid_off = True
        self.paid_off_at = datetime.now()
        self.payoff_event_id = event_id


class EvidenceChain(BaseModel):
    """证据链"""
    chain_id: str = Field(default_factory=lambda: str(uuid4()))
    target_conclusion: str  # 要证明的结论

    # 证据节点
    evidence_nodes: List[str] = Field(default_factory=list)  # clue_id列表

    # 逻辑关系
    logic_type: Literal["sequential", "convergent", "elimination"]
    # sequential: A→B→C (顺序推理)
    # convergent: A+B+C→D (多证据汇聚)
    # elimination: 排除法

    # 完整性
    completeness: float = 0.0  # 0-1, 收集进度

    # 验证状态
    validated: bool = False

    def add_evidence(self, clue_id: str):
        """添加证据"""
        if clue_id not in self.evidence_nodes:
            self.evidence_nodes.append(clue_id)
            self._update_completeness()

    def _update_completeness(self):
        """更新完整性"""
        # 简化计算，实际可根据logic_type定制
        required_count = 3  # 假设需要3个证据
        self.completeness = min(1.0, len(self.evidence_nodes) / required_count)

    def can_validate(self) -> bool:
        """是否可以验证"""
        return self.completeness >= 0.8  # 80%以上可验证


# ============================================================================
# 线索经济管理器
# ============================================================================

class ClueEconomyManager(BaseModel):
    """线索经济管理器"""

    # 线索池
    clues: Dict[str, ClueInstance] = Field(default_factory=dict)

    # 伏笔债务池
    setup_debts: Dict[str, SetupDebt] = Field(default_factory=dict)

    # 证据链
    evidence_chains: Dict[str, EvidenceChain] = Field(default_factory=dict)

    # 红鲱鱼配额
    red_herring_cap: int = 2  # 同时存在的红鲱鱼上限
    active_red_herrings: int = 0

    # 全局回合数
    global_turn: int = 0

    # ========================================================================
    # 线索管理
    # ========================================================================

    def register_clue(
        self,
        content: str,
        clue_type: Literal["implicit", "explicit", "red_herring"],
        related_secret: Optional[str] = None,
        verification_method: Optional[str] = None
    ) -> ClueInstance:
        """注册新线索"""

        # 检查红鲱鱼配额
        if clue_type == "red_herring" and self.active_red_herrings >= self.red_herring_cap:
            # 降级为隐性线索
            clue_type = "implicit"

        clue = ClueInstance(
            content=content,
            clue_type=clue_type,
            related_secret=related_secret,
            verification_method=verification_method,
            reliability=0.3 if clue_type == "red_herring" else 1.0
        )

        self.clues[clue.clue_id] = clue

        if clue_type == "red_herring":
            self.active_red_herrings += 1

        return clue

    def discover_clue(self, clue_id: str):
        """主角发现线索"""
        if clue_id in self.clues:
            clue = self.clues[clue_id]
            clue.discovered = True
            clue.discovered_at = datetime.now()

    def verify_clue(self, clue_id: str) -> bool:
        """验证线索真伪"""
        if clue_id not in self.clues:
            return False

        clue = self.clues[clue_id]
        clue.verified = True

        # 如果是红鲱鱼，被验证后可以排除
        if clue.clue_type == "red_herring":
            self.active_red_herrings -= 1

        return clue.reliability > 0.5

    def get_discovered_clues(self) -> List[ClueInstance]:
        """获取已发现的线索"""
        return [c for c in self.clues.values() if c.discovered]

    def get_unverified_clues(self) -> List[ClueInstance]:
        """获取未验证的线索"""
        return [c for c in self.clues.values() if c.discovered and not c.verified]

    # ========================================================================
    # 伏笔债务管理
    # ========================================================================

    def create_setup(
        self,
        description: str,
        setup_type: Literal["foreshadowing", "promise", "mystery", "question"],
        deadline_turns: int = 20,
        priority: Literal["low", "medium", "high", "critical"] = "medium"
    ) -> SetupDebt:
        """创建伏笔债务"""

        setup = SetupDebt(
            description=description,
            setup_type=setup_type,
            deadline_turns=deadline_turns,
            priority=priority
        )

        self.setup_debts[setup.setup_id] = setup
        return setup

    def pay_off_setup(self, setup_id: str, event_id: str):
        """兑现伏笔"""
        if setup_id in self.setup_debts:
            self.setup_debts[setup_id].pay_off(event_id)

    def get_overdue_setups(self) -> List[SetupDebt]:
        """获取逾期伏笔"""
        return [s for s in self.setup_debts.values() if s.is_overdue]

    def get_urgent_setups(self, threshold: float = 0.7) -> List[SetupDebt]:
        """获取紧迫伏笔"""
        return [
            s for s in self.setup_debts.values()
            if not s.paid_off and s.urgency >= threshold
        ]

    def get_pending_setups(self) -> List[SetupDebt]:
        """获取待兑现伏笔"""
        return [s for s in self.setup_debts.values() if not s.paid_off]

    def tick_all_setups(self):
        """推进所有伏笔的回合计数"""
        for setup in self.setup_debts.values():
            setup.tick()
        self.global_turn += 1

    def get_debt_stats(self) -> Dict[str, int]:
        """获取债务统计"""
        total = len(self.setup_debts)
        paid = len([s for s in self.setup_debts.values() if s.paid_off])
        overdue = len(self.get_overdue_setups())
        urgent = len(self.get_urgent_setups())

        return {
            "total": total,
            "paid_off": paid,
            "pending": total - paid,
            "overdue": overdue,
            "urgent": urgent,
            "payoff_rate": paid / total if total > 0 else 0
        }

    # ========================================================================
    # 证据链管理
    # ========================================================================

    def create_evidence_chain(
        self,
        target_conclusion: str,
        logic_type: Literal["sequential", "convergent", "elimination"] = "convergent"
    ) -> EvidenceChain:
        """创建证据链"""

        chain = EvidenceChain(
            target_conclusion=target_conclusion,
            logic_type=logic_type
        )

        self.evidence_chains[chain.chain_id] = chain
        return chain

    def add_evidence_to_chain(self, chain_id: str, clue_id: str):
        """向证据链添加证据"""
        if chain_id in self.evidence_chains and clue_id in self.clues:
            self.evidence_chains[chain_id].add_evidence(clue_id)

    def validate_chain(self, chain_id: str) -> bool:
        """验证证据链"""
        if chain_id not in self.evidence_chains:
            return False

        chain = self.evidence_chains[chain_id]

        if not chain.can_validate():
            return False

        # 检查所有证据是否已验证
        all_verified = all(
            self.clues.get(clue_id, ClueInstance(content="")).verified
            for clue_id in chain.evidence_nodes
        )

        if all_verified:
            chain.validated = True
            return True

        return False

    def get_active_chains(self) -> List[EvidenceChain]:
        """获取活跃证据链"""
        return [c for c in self.evidence_chains.values() if not c.validated]

    # ========================================================================
    # 综合分析
    # ========================================================================

    def get_economy_health(self) -> Dict[str, float]:
        """获取线索经济健康度"""

        debt_stats = self.get_debt_stats()

        # 伏笔偿还率(越高越好)
        payoff_rate = debt_stats["payoff_rate"]

        # 逾期率(越低越好)
        overdue_rate = debt_stats["overdue"] / debt_stats["total"] if debt_stats["total"] > 0 else 0

        # 线索发现率
        total_clues = len(self.clues)
        discovered_clues = len(self.get_discovered_clues())
        discovery_rate = discovered_clues / total_clues if total_clues > 0 else 0

        # 证据链完成度
        total_chains = len(self.evidence_chains)
        validated_chains = len([c for c in self.evidence_chains.values() if c.validated])
        chain_completion = validated_chains / total_chains if total_chains > 0 else 0

        # 综合健康度(0-1)
        health_score = (
            payoff_rate * 0.4 +
            (1 - overdue_rate) * 0.3 +
            discovery_rate * 0.15 +
            chain_completion * 0.15
        )

        return {
            "overall_health": health_score,
            "payoff_rate": payoff_rate,
            "overdue_rate": overdue_rate,
            "discovery_rate": discovery_rate,
            "chain_completion": chain_completion
        }

    def suggest_next_clues(self) -> List[str]:
        """建议下一步应投放的线索"""
        suggestions = []

        # 1. 检查逾期伏笔,建议投放相关线索
        overdue = self.get_overdue_setups()
        for setup in overdue[:2]:  # 最多2个
            suggestions.append(f"投放线索兑现伏笔: {setup.description[:30]}...")

        # 2. 检查未完成证据链
        active_chains = self.get_active_chains()
        for chain in active_chains:
            if chain.completeness < 0.8:
                suggestions.append(f"补充证据链: {chain.target_conclusion[:30]}...")

        # 3. 红鲱鱼配额检查
        if self.active_red_herrings < self.red_herring_cap:
            suggestions.append("可投放红鲱鱼增加悬念")

        return suggestions[:5]  # 最多5条建议
