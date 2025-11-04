"""全局导演（Global Director）

根据 TECHNICAL_IMPLEMENTATION_PLAN.md Section 2 设计
核心功能：
1. 事件调度与评分
2. 一致性审计
3. 线索经济管理
4. 主调度循环
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..models.world_state import WorldState
from ..models.event_node import EventNode, EventArc, EventStatus
from ..models.clue import ClueRegistry

from .event_scoring import EventScorer, ScoringMode, EventScore
from .consistency_auditor import ConsistencyAuditor, AuditReport
from .clue_economy_manager import ClueEconomyManager


class DirectorMode(Enum):
    """导演模式"""
    PLAYABILITY_FIRST = "playability_first"  # 可玩性优先
    NARRATIVE_FIRST = "narrative_first"      # 叙事优先
    BALANCED = "balanced"                    # 平衡模式


@dataclass
class DirectorConfig:
    """导演配置"""
    mode: DirectorMode = DirectorMode.BALANCED
    genre: str = "scifi"  # scifi 或 xianxia

    # 评分权重（可选，覆盖默认值）
    scoring_weights: Optional[Dict[str, float]] = None

    # 一致性检查
    enable_consistency_audit: bool = True
    block_on_critical_violations: bool = True

    # 线索经济
    enable_clue_economy: bool = True
    setup_sla_default: int = 20  # 默认伏笔 SLA（回合数）

    # 事件选择
    max_parallel_events: int = 3  # 同时活跃的事件上限
    min_event_score: float = 40.0  # 最低事件分数阈值


@dataclass
class DirectorDecision:
    """导演决策结果"""
    selected_event: Optional[EventNode] = None
    score: Optional[EventScore] = None
    audit_report: Optional[AuditReport] = None
    reasoning: str = ""
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class GlobalDirector:
    """全局导演

    整合事件评分、一致性审计、线索经济管理
    负责在每个回合选择最优事件并确保一致性
    """

    def __init__(
        self,
        config: DirectorConfig,
        setting: Dict[str, Any],
        registry: Optional[ClueRegistry] = None
    ):
        """初始化全局导演

        Args:
            config: 导演配置
            setting: 小说设定
            registry: 线索注册表（可选）
        """
        self.config = config
        self.setting = setting
        self.current_turn = 0

        # 初始化子系统
        self._init_subsystems(registry)

        # 事件历史
        self.completed_events: List[str] = []
        self.active_events: List[EventNode] = []

        # 决策历史
        self.decision_history: List[DirectorDecision] = []

    def _init_subsystems(self, registry: Optional[ClueRegistry]):
        """初始化子系统"""
        # 1. 事件评分器
        scoring_mode = self._get_scoring_mode()
        self.scorer = EventScorer(
            mode=scoring_mode,
            genre=self.config.genre,
            weights=self.config.scoring_weights
        )

        # 2. 一致性审计器
        self.auditor = ConsistencyAuditor(setting=self.setting)

        # 3. 线索经济管理器
        self.clue_manager = ClueEconomyManager(registry=registry)

    def _get_scoring_mode(self) -> ScoringMode:
        """将 DirectorMode 转换为 ScoringMode"""
        mode_map = {
            DirectorMode.PLAYABILITY_FIRST: ScoringMode.PLAYABILITY,
            DirectorMode.NARRATIVE_FIRST: ScoringMode.NARRATIVE,
            DirectorMode.BALANCED: ScoringMode.HYBRID
        }
        return mode_map.get(self.config.mode, ScoringMode.HYBRID)

    # ========================================================================
    # 主调度循环
    # ========================================================================

    def select_next_event(
        self,
        world_state: WorldState,
        available_events: List[EventNode]
    ) -> DirectorDecision:
        """选择下一个事件

        主调度循环的核心方法

        Args:
            world_state: 当前世界状态
            available_events: 可用事件列表

        Returns:
            DirectorDecision: 导演决策
        """
        decision = DirectorDecision()

        # 1. 过滤可用事件
        candidates = self._filter_available_events(
            available_events,
            world_state
        )

        if not candidates:
            decision.reasoning = "没有可用事件"
            decision.warnings.append("事件池为空，可能需要生成新事件")
            return decision

        # 2. 评分候选事件
        scored_events = self._score_candidates(candidates, world_state)

        if not scored_events:
            decision.reasoning = "所有事件评分低于阈值"
            decision.warnings.append(f"所有事件分数低于 {self.config.min_event_score}")
            return decision

        # 3. 选择最高分事件
        best_event, best_score = scored_events[0]
        decision.selected_event = best_event
        decision.score = best_score

        # 4. 一致性审计
        if self.config.enable_consistency_audit:
            audit = self.auditor.audit_world_state(world_state, best_event)
            decision.audit_report = audit

            # 如果有致命违规且配置阻止执行
            if not audit.passed and self.config.block_on_critical_violations:
                decision.selected_event = None
                decision.reasoning = f"一致性审计失败: {audit.summary}"
                decision.warnings.extend(audit.recommendations)
                return decision

            # 非阻塞违规，记录警告
            if audit.violations:
                decision.warnings.append(audit.summary)

        # 5. 检查线索经济
        if self.config.enable_clue_economy:
            clue_suggestions = self.clue_manager.get_suggestions()
            decision.suggestions.extend(clue_suggestions)

        # 6. 生成决策说明
        decision.reasoning = self._generate_decision_reasoning(
            best_event,
            best_score,
            scored_events
        )

        # 记录决策
        self.decision_history.append(decision)

        return decision

    def _filter_available_events(
        self,
        events: List[EventNode],
        world_state: WorldState
    ) -> List[EventNode]:
        """过滤可用事件

        Args:
            events: 候选事件列表
            world_state: 当前世界状态

        Returns:
            List[EventNode]: 满足前置条件的事件
        """
        candidates = []

        for event in events:
            # 跳过已完成或失败的事件
            if event.status in [EventStatus.COMPLETED, EventStatus.FAILED]:
                continue

            # 检查是否满足前置条件
            if event.is_available(world_state, self.completed_events):
                candidates.append(event)

        return candidates

    def _score_candidates(
        self,
        candidates: List[EventNode],
        world_state: WorldState
    ) -> List[Tuple[EventNode, EventScore]]:
        """评分候选事件

        Args:
            candidates: 候选事件
            world_state: 当前世界状态

        Returns:
            List[Tuple[EventNode, EventScore]]: 评分后的事件列表，按分数降序排序
        """
        context = {
            "world_state": world_state,
            "current_turn": self.current_turn,
            "completed_events": self.completed_events,
            "active_events": self.active_events
        }

        scored = self.scorer.rank_events(candidates, context)

        # 过滤低于阈值的事件
        scored = [
            (event, score) for event, score in scored
            if score.total_score >= self.config.min_event_score
        ]

        return scored

    def _generate_decision_reasoning(
        self,
        selected_event: EventNode,
        score: EventScore,
        alternatives: List[Tuple[EventNode, EventScore]]
    ) -> str:
        """生成决策说明

        Args:
            selected_event: 选中的事件
            score: 评分结果
            alternatives: 备选方案

        Returns:
            str: 决策说明
        """
        lines = []

        lines.append(f"选择事件: {selected_event.title}")
        lines.append(f"总分: {score.total_score:.1f}/100")
        lines.append(f"评分理由: {score.reasoning}")

        if len(alternatives) > 1:
            lines.append(f"\n备选方案 ({len(alternatives) - 1} 个):")
            for event, alt_score in alternatives[1:4]:  # 最多显示 3 个
                lines.append(
                    f"  - {event.title}: {alt_score.total_score:.1f}/100"
                )

        return "\n".join(lines)

    # ========================================================================
    # 事件执行
    # ========================================================================

    def execute_event(
        self,
        event: EventNode,
        world_state: WorldState
    ) -> bool:
        """执行事件

        Args:
            event: 要执行的事件
            world_state: 当前世界状态

        Returns:
            bool: 是否成功执行
        """
        # 标记为进行中
        event.status = EventStatus.IN_PROGRESS
        self.active_events.append(event)

        # 应用事件效果
        if event.effects:
            world_state.apply_state_patch(event.effects)

        # 记录事件
        world_state.add_event({
            "event_id": event.id,
            "title": event.title,
            "status": "in_progress"
        })

        return True

    def complete_event(
        self,
        event: EventNode,
        world_state: WorldState,
        success: bool = True
    ):
        """完成事件

        Args:
            event: 完成的事件
            world_state: 当前世界状态
            success: 是否成功完成
        """
        # 更新状态
        event.status = EventStatus.COMPLETED if success else EventStatus.FAILED

        # 从活跃列表移除
        if event in self.active_events:
            self.active_events.remove(event)

        # 添加到已完成列表
        if success:
            self.completed_events.append(event.id)

            # 应用奖励
            if event.rewards:
                world_state.apply_state_patch({"resources": event.rewards})

        # 处理线索经济
        if self.config.enable_clue_economy:
            # 偿还伏笔
            for setup_id in event.payoffs:
                self.clue_manager.pay_off_setup(setup_id, event.id)

            # 发现线索
            for clue_id in event.clues:
                self.clue_manager.discover_clue(clue_id)

        # 更新世界状态事件日志
        for log_entry in world_state.events_log:
            if log_entry.get("event_id") == event.id:
                log_entry["status"] = "completed" if success else "failed"
                break

        # 推进回合
        self.advance_turn()

    # ========================================================================
    # 事件线管理
    # ========================================================================

    def select_event_from_arcs(
        self,
        arcs: List[EventArc],
        world_state: WorldState
    ) -> DirectorDecision:
        """从事件线中选择事件

        Args:
            arcs: 事件线列表
            world_state: 当前世界状态

        Returns:
            DirectorDecision: 导演决策
        """
        # 收集所有事件线的下一个事件
        candidates = []

        for arc in arcs:
            if arc.completed:
                continue

            next_event = arc.get_next_event(world_state, self.completed_events)
            if next_event:
                candidates.append(next_event)

        # 使用标准选择流程
        return self.select_next_event(world_state, candidates)

    def get_arc_progress(self, arcs: List[EventArc]) -> Dict[str, float]:
        """获取所有事件线的进度

        Args:
            arcs: 事件线列表

        Returns:
            Dict[str, float]: {arc_id: progress}
        """
        return {
            arc.id: arc.get_progress()
            for arc in arcs
        }

    # ========================================================================
    # 状态管理
    # ========================================================================

    def advance_turn(self, turns: int = 1):
        """推进回合

        Args:
            turns: 推进的回合数
        """
        self.current_turn += turns

        # 同步线索管理器
        if self.config.enable_clue_economy:
            self.clue_manager.advance_turn(turns)

    def get_status(self) -> Dict[str, Any]:
        """获取导演状态

        Returns:
            Dict: 状态信息
        """
        status = {
            "current_turn": self.current_turn,
            "mode": self.config.mode.value,
            "genre": self.config.genre,
            "completed_events": len(self.completed_events),
            "active_events": len(self.active_events),
            "decisions_made": len(self.decision_history)
        }

        # 一致性统计
        if self.config.enable_consistency_audit:
            violation_stats = self.auditor.get_violation_stats()
            status["consistency"] = violation_stats

        # 线索经济统计
        if self.config.enable_clue_economy:
            clue_stats = self.clue_manager.get_stats()
            status["clue_economy"] = clue_stats

        return status

    def get_health_report(self) -> Dict[str, Any]:
        """获取健康报告

        Returns:
            Dict: 包含各子系统健康状态的报告
        """
        report = {
            "overall_status": "healthy",
            "issues": [],
            "recommendations": []
        }

        # 检查线索经济
        if self.config.enable_clue_economy:
            metrics = self.clue_manager.get_health_metrics()

            if metrics.overall_health < 60:
                report["overall_status"] = "needs_attention"
                report["issues"].append(
                    f"线索经济健康度低: {metrics.overall_health:.1f}/100"
                )

            if metrics.overdue_setups > 0:
                report["issues"].append(
                    f"有 {metrics.overdue_setups} 个伏笔逾期"
                )

            report["recommendations"].extend(
                self.clue_manager.get_suggestions()
            )

        # 检查一致性
        if self.config.enable_consistency_audit:
            stats = self.auditor.get_violation_stats()

            critical_count = stats.get("by_severity", {}).get("critical", 0)
            if critical_count > 0:
                report["overall_status"] = "critical"
                report["issues"].append(
                    f"有 {critical_count} 个致命一致性违规"
                )

        return report

    # ========================================================================
    # 导出/导入
    # ========================================================================

    def export_state(self) -> Dict[str, Any]:
        """导出状态（用于持久化）"""
        state = {
            "current_turn": self.current_turn,
            "config": {
                "mode": self.config.mode.value,
                "genre": self.config.genre,
            },
            "completed_events": self.completed_events,
            "decision_count": len(self.decision_history)
        }

        if self.config.enable_clue_economy:
            state["clue_economy"] = self.clue_manager.export_state()

        return state
