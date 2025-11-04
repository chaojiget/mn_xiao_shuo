"""线索经济管理器

根据 TECHNICAL_IMPLEMENTATION_PLAN.md Section 2.5 设计
管理伏笔（Setup）的 SLA、线索（Clue）的发现和验证、证据链、健康度监控
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from ..models.clue import (
    Clue, ClueStatus, Evidence, Setup, SetupStatus, ClueRegistry
)


@dataclass
class ClueHealthMetrics:
    """线索经济健康度指标"""
    # 伏笔相关
    total_setups: int = 0
    paid_setups: int = 0
    overdue_setups: int = 0
    payoff_rate: float = 0.0  # 偿还率

    # 线索相关
    total_clues: int = 0
    discovered_clues: int = 0
    verified_clues: int = 0
    discovery_rate: float = 0.0

    # 综合健康度 (0-100)
    overall_health: float = 0.0

    # 问题指标
    overdue_rate: float = 0.0
    urgent_setups: int = 0


class ClueEconomyManager:
    """线索经济管理器

    核心功能：
    1. 管理伏笔（Setup）的 SLA 截止时间
    2. 跟踪线索（Clue）的发现和验证
    3. 证据链验证
    4. 健康度监控和建议生成
    """

    def __init__(self, registry: Optional[ClueRegistry] = None):
        """初始化管理器

        Args:
            registry: 线索注册表，如果为 None 则创建新的
        """
        self.registry = registry or ClueRegistry()
        self.current_turn = 0

    # ========================================================================
    # 伏笔管理
    # ========================================================================

    def create_setup(
        self,
        description: str,
        setup_event_id: str,
        sla_deadline: int = 20,
        priority: float = 1.0,
        setup_type: str = "plot"
    ) -> Setup:
        """创建新伏笔

        Args:
            description: 伏笔描述
            setup_event_id: 埋伏笔的事件 ID
            sla_deadline: SLA 截止回合数（默认 20 回合）
            priority: 优先级（0-1，越高越重要）
            setup_type: 类型（plot/character/world）

        Returns:
            Setup: 创建的伏笔对象
        """
        setup = Setup(
            id=f"setup_{len(self.registry.setups)}",
            description=description,
            setup_event_id=setup_event_id,
            sla_deadline=sla_deadline,
            setup_turn=self.current_turn,
            priority=priority,
            type=setup_type
        )

        self.registry.add_setup(setup)
        return setup

    def pay_off_setup(self, setup_id: str, payoff_event_id: str) -> bool:
        """偿还伏笔

        Args:
            setup_id: 伏笔 ID
            payoff_event_id: 偿还事件 ID

        Returns:
            bool: 是否成功偿还
        """
        if setup_id not in self.registry.setups:
            return False

        setup = self.registry.setups[setup_id]

        if setup.status == SetupStatus.PAID_OFF:
            return False  # 已经偿还过

        setup.payoff_event_id = payoff_event_id
        setup.payoff_turn = self.current_turn
        setup.status = SetupStatus.PAID_OFF

        return True

    def get_overdue_setups(self) -> List[Setup]:
        """获取逾期的伏笔"""
        return self.registry.get_overdue_setups(self.current_turn)

    def get_urgent_setups(self, urgency_threshold: float = 0.7) -> List[Setup]:
        """获取紧迫的伏笔

        Args:
            urgency_threshold: 紧迫度阈值（0-1）

        Returns:
            List[Setup]: 紧迫伏笔列表
        """
        urgent = []
        for setup in self.registry.setups.values():
            if setup.status == SetupStatus.PAID_OFF:
                continue

            remaining = setup.remaining_turns(self.current_turn)
            if remaining <= 0:
                continue  # 已逾期的在 overdue 里

            urgency = 1.0 - (remaining / setup.sla_deadline)
            if urgency >= urgency_threshold:
                urgent.append(setup)

        # 按紧迫度和优先级排序
        urgent.sort(
            key=lambda s: (
                -s.priority,  # 优先级高的在前
                s.remaining_turns(self.current_turn)  # 剩余时间短的在前
            )
        )

        return urgent

    def get_pending_setups(self) -> List[Setup]:
        """获取所有待偿还的伏笔"""
        return [
            s for s in self.registry.setups.values()
            if s.status != SetupStatus.PAID_OFF
        ]

    # ========================================================================
    # 线索管理
    # ========================================================================

    def register_clue(
        self,
        content: str,
        clue_type: str,
        related_event: Optional[str] = None,
        verification_method: str = "",
        evidence_ids: Optional[List[str]] = None
    ) -> Clue:
        """注册新线索

        Args:
            content: 线索内容
            clue_type: 线索类型
            related_event: 关联事件
            verification_method: 验证方法
            evidence_ids: 证据 ID 列表

        Returns:
            Clue: 创建的线索对象
        """
        clue = Clue(
            id=f"clue_{len(self.registry.clues)}",
            content=content,
            type=clue_type,
            related_event=related_event,
            verification_method=verification_method,
            evidence_ids=evidence_ids or []
        )

        self.registry.add_clue(clue)
        return clue

    def discover_clue(self, clue_id: str) -> bool:
        """发现线索

        Args:
            clue_id: 线索 ID

        Returns:
            bool: 是否成功发现
        """
        if clue_id not in self.registry.clues:
            return False

        clue = self.registry.clues[clue_id]
        if clue.status != ClueStatus.HIDDEN:
            return False  # 已经发现过

        clue.status = ClueStatus.DISCOVERED
        from datetime import datetime
        clue.discovered_at = datetime.now()

        return True

    def verify_clue(self, clue_id: str, evidence: List[Evidence]) -> bool:
        """验证线索

        Args:
            clue_id: 线索 ID
            evidence: 可用证据列表

        Returns:
            bool: 是否验证成功
        """
        if clue_id not in self.registry.clues:
            return False

        clue = self.registry.clues[clue_id]
        return clue.verify(evidence)

    def get_discovered_clues(self) -> List[Clue]:
        """获取已发现的线索"""
        return self.registry.get_discovered_clues()

    def get_unverified_clues(self) -> List[Clue]:
        """获取已发现但未验证的线索"""
        return [
            c for c in self.registry.clues.values()
            if c.status == ClueStatus.DISCOVERED
        ]

    # ========================================================================
    # 证据管理
    # ========================================================================

    def register_evidence(
        self,
        content: str,
        evidence_type: str,
        source: str,
        credibility: float = 1.0,
        related_clues: Optional[List[str]] = None
    ) -> Evidence:
        """注册新证据

        Args:
            content: 证据内容
            evidence_type: 证据类型（data/testimony/physical/document）
            source: 来源
            credibility: 可信度（0-1）
            related_clues: 关联线索 ID 列表

        Returns:
            Evidence: 创建的证据对象
        """
        evidence = Evidence(
            id=f"evidence_{len(self.registry.evidence)}",
            content=content,
            type=evidence_type,
            source=source,
            credibility=credibility,
            related_clues=related_clues or []
        )

        self.registry.add_evidence(evidence)
        return evidence

    def validate_evidence_chain(self, clue_id: str) -> tuple[bool, List[str]]:
        """验证线索的证据链

        Args:
            clue_id: 线索 ID

        Returns:
            tuple[bool, List[str]]: (是否完整, 缺失的证据 ID 列表)
        """
        if clue_id not in self.registry.clues:
            return False, []

        clue = self.registry.clues[clue_id]
        missing = []

        for evidence_id in clue.evidence_ids:
            if evidence_id not in self.registry.evidence:
                missing.append(evidence_id)

        return len(missing) == 0, missing

    # ========================================================================
    # 健康度监控
    # ========================================================================

    def get_health_metrics(self) -> ClueHealthMetrics:
        """获取线索经济健康度指标

        Returns:
            ClueHealthMetrics: 健康度指标
        """
        metrics = ClueHealthMetrics()

        # 伏笔统计
        all_setups = list(self.registry.setups.values())
        metrics.total_setups = len(all_setups)
        metrics.paid_setups = sum(1 for s in all_setups if s.status == SetupStatus.PAID_OFF)
        metrics.overdue_setups = len(self.get_overdue_setups())
        metrics.urgent_setups = len(self.get_urgent_setups())

        if metrics.total_setups > 0:
            metrics.payoff_rate = metrics.paid_setups / metrics.total_setups
            metrics.overdue_rate = metrics.overdue_setups / metrics.total_setups
        else:
            metrics.payoff_rate = 1.0
            metrics.overdue_rate = 0.0

        # 线索统计
        all_clues = list(self.registry.clues.values())
        metrics.total_clues = len(all_clues)
        metrics.discovered_clues = sum(
            1 for c in all_clues
            if c.status in [ClueStatus.DISCOVERED, ClueStatus.VERIFIED]
        )
        metrics.verified_clues = sum(1 for c in all_clues if c.status == ClueStatus.VERIFIED)

        if metrics.total_clues > 0:
            metrics.discovery_rate = metrics.discovered_clues / metrics.total_clues
        else:
            metrics.discovery_rate = 1.0

        # 综合健康度计算（0-100）
        # 伏笔偿还率 40%、逾期率 30%、线索发现率 30%
        health_score = (
            metrics.payoff_rate * 40 +
            (1 - metrics.overdue_rate) * 30 +
            metrics.discovery_rate * 30
        )

        # 严重扣分：每个逾期伏笔扣 5 分
        health_score -= metrics.overdue_setups * 5

        metrics.overall_health = max(0.0, min(100.0, health_score))

        return metrics

    def get_suggestions(self) -> List[str]:
        """生成改进建议

        Returns:
            List[str]: 建议列表
        """
        suggestions = []

        # 1. 检查逾期伏笔
        overdue = self.get_overdue_setups()
        if overdue:
            suggestions.append(
                f"【紧急】有 {len(overdue)} 个伏笔已逾期，需要立即偿还"
            )
            for setup in overdue[:3]:  # 最多显示 3 个
                remaining = abs(setup.remaining_turns(self.current_turn))
                suggestions.append(
                    f"  - 伏笔 '{setup.description[:30]}...' 已逾期 {remaining} 回合"
                )

        # 2. 检查紧迫伏笔
        urgent = self.get_urgent_setups()
        if urgent and not overdue:  # 如果没有逾期才提示紧迫
            suggestions.append(
                f"【警告】有 {len(urgent)} 个伏笔即将到期"
            )
            for setup in urgent[:3]:
                remaining = setup.remaining_turns(self.current_turn)
                suggestions.append(
                    f"  - 伏笔 '{setup.description[:30]}...' 还剩 {remaining} 回合"
                )

        # 3. 检查未验证线索
        unverified = self.get_unverified_clues()
        if len(unverified) >= 3:
            suggestions.append(
                f"【提示】有 {len(unverified)} 个线索已发现但未验证"
            )

        # 4. 检查整体健康度
        metrics = self.get_health_metrics()
        if metrics.overall_health < 60:
            suggestions.append(
                f"【警告】线索经济健康度较低 ({metrics.overall_health:.1f}/100)"
            )

        # 5. 具体改进建议
        if metrics.payoff_rate < 0.5 and metrics.total_setups > 0:
            suggestions.append("【建议】伏笔偿还率低，考虑在后续章节中偿还更多伏笔")

        if metrics.discovery_rate < 0.3 and metrics.total_clues > 5:
            suggestions.append("【建议】线索发现率低，考虑增加线索投放或降低发现难度")

        if not suggestions:
            suggestions.append("【良好】线索经济状况健康")

        return suggestions

    # ========================================================================
    # 回合管理
    # ========================================================================

    def advance_turn(self, turns: int = 1):
        """推进回合

        Args:
            turns: 推进的回合数（默认 1）
        """
        self.current_turn += turns

        # 更新伏笔状态
        for setup in self.registry.setups.values():
            if setup.is_overdue(self.current_turn) and setup.status != SetupStatus.PAID_OFF:
                setup.status = SetupStatus.OVERDUE

    # ========================================================================
    # 工具方法
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            Dict: 统计数据
        """
        metrics = self.get_health_metrics()

        return {
            "current_turn": self.current_turn,
            "setups": {
                "total": metrics.total_setups,
                "paid": metrics.paid_setups,
                "pending": metrics.total_setups - metrics.paid_setups,
                "overdue": metrics.overdue_setups,
                "urgent": metrics.urgent_setups,
                "payoff_rate": f"{metrics.payoff_rate * 100:.1f}%"
            },
            "clues": {
                "total": metrics.total_clues,
                "discovered": metrics.discovered_clues,
                "verified": metrics.verified_clues,
                "discovery_rate": f"{metrics.discovery_rate * 100:.1f}%"
            },
            "health": {
                "overall": f"{metrics.overall_health:.1f}/100",
                "status": self._get_health_status(metrics.overall_health)
            }
        }

    def _get_health_status(self, health_score: float) -> str:
        """获取健康状态描述"""
        if health_score >= 80:
            return "优秀"
        elif health_score >= 60:
            return "良好"
        elif health_score >= 40:
            return "一般"
        else:
            return "较差"

    def export_state(self) -> Dict[str, Any]:
        """导出状态（用于持久化）"""
        return {
            "current_turn": self.current_turn,
            "registry": {
                "clues": {k: v.__dict__ for k, v in self.registry.clues.items()},
                "evidence": {k: v.__dict__ for k, v in self.registry.evidence.items()},
                "setups": {k: v.__dict__ for k, v in self.registry.setups.items()}
            }
        }
