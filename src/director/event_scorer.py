"""
事件线评分系统
Event Arc Scoring System

支持三种评分模式:
A) 偏可玩性 (Playability-focused)
B) 偏叙事 (Narrative-focused)
C) 混合模式 (Hybrid)

核心指标:
- 可玩性: PuzzleDensity, SkillChecksVariety, FailureGrace, HintLatency, ExploitResistance, RewardLoop
- 叙事性: ArcProgress, ThemeEcho, ConflictGradient, PayoffDebt, SceneSpecificity, PacingSmoothness
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass


# ============================================================================
# 评分指标定义
# ============================================================================

@dataclass
class PlayabilityMetrics:
    """可玩性指标"""
    puzzle_density: float = 0.0  # 谜题密度 (0-1)
    skill_checks_variety: float = 0.0  # 技能检定多样性 (0-1)
    failure_grace: float = 0.0  # 失败宽容度 (0-1, 高=允许失败后继续)
    hint_latency: float = 0.0  # 提示延迟 (0-1, 低=更快给提示)
    exploit_resistance: float = 0.0  # 防刷抗性 (0-1)
    reward_loop: float = 0.0  # 奖励循环质量 (0-1)

    def overall_score(self) -> float:
        """总体可玩性得分"""
        return (
            self.puzzle_density * 0.2 +
            self.skill_checks_variety * 0.2 +
            self.failure_grace * 0.15 +
            self.hint_latency * 0.15 +
            self.exploit_resistance * 0.15 +
            self.reward_loop * 0.15
        )


@dataclass
class NarrativeMetrics:
    """叙事性指标"""
    arc_progress: float = 0.0  # 事件线推进度 (0-1)
    theme_echo: float = 0.0  # 主题回响 (0-1)
    conflict_gradient: float = 0.0  # 冲突梯度 (0-1, 是否递增)
    payoff_debt: float = 0.0  # 伏笔偿还率 (0-1, 高=伏笔得到兑现)
    scene_specificity: float = 0.0  # 场景具体性 (0-1)
    pacing_smoothness: float = 0.0  # 节奏平滑度 (0-1)

    def overall_score(self) -> float:
        """总体叙事性得分"""
        return (
            self.arc_progress * 0.2 +
            self.theme_echo * 0.15 +
            self.conflict_gradient * 0.2 +
            self.payoff_debt * 0.2 +
            self.scene_specificity * 0.15 +
            self.pacing_smoothness * 0.1
        )


class EventScore(BaseModel):
    """事件评分"""
    event_id: str
    playability: PlayabilityMetrics
    narrative: NarrativeMetrics

    # 综合得分 (根据权重计算)
    weighted_score: float = 0.0

    # 额外因素
    tension_delta: float = 0.0  # 张力变化 (-1 to 1)
    resource_cost: float = 0.0  # 资源消耗 (0-1)
    stall_risk: float = 0.0  # 停滞风险 (0-1, 高=可能卡住玩家)

    def calculate_weighted_score(
        self,
        playability_weight: float = 0.6,
        narrative_weight: float = 0.4
    ) -> float:
        """计算加权总分"""
        playability_score = self.playability.overall_score()
        narrative_score = self.narrative.overall_score()

        base_score = (
            playability_score * playability_weight +
            narrative_score * narrative_weight
        )

        # 调整：停滞风险高的扣分
        stall_penalty = self.stall_risk * 0.2

        # 调整：张力提升的加分
        tension_bonus = max(0, self.tension_delta) * 0.1

        self.weighted_score = max(0, base_score - stall_penalty + tension_bonus)
        return self.weighted_score


# ============================================================================
# 事件评分器
# ============================================================================

class EventScorer:
    """事件评分器"""

    def __init__(
        self,
        preference: Literal["playability", "narrative", "hybrid"] = "hybrid",
        playability_weight: float = 0.6,
        narrative_weight: float = 0.4
    ):
        self.preference = preference
        self.playability_weight = playability_weight
        self.narrative_weight = narrative_weight

        # 根据偏好调整权重
        if preference == "playability":
            self.playability_weight = 0.7
            self.narrative_weight = 0.3
        elif preference == "narrative":
            self.playability_weight = 0.4
            self.narrative_weight = 0.6

    def score_event(
        self,
        event_data: Dict,
        world_state: Dict,
        history: Dict
    ) -> EventScore:
        """评分单个事件"""

        # 计算可玩性指标
        playability = self._calculate_playability(event_data, world_state, history)

        # 计算叙事性指标
        narrative = self._calculate_narrative(event_data, world_state, history)

        # 计算额外因素
        tension_delta = self._calculate_tension_delta(event_data, world_state)
        resource_cost = self._calculate_resource_cost(event_data, world_state)
        stall_risk = self._calculate_stall_risk(event_data, world_state, history)

        # 创建评分对象
        score = EventScore(
            event_id=event_data.get("event_id", "unknown"),
            playability=playability,
            narrative=narrative,
            tension_delta=tension_delta,
            resource_cost=resource_cost,
            stall_risk=stall_risk
        )

        # 计算加权总分
        score.calculate_weighted_score(
            self.playability_weight,
            self.narrative_weight
        )

        return score

    def _calculate_playability(
        self,
        event_data: Dict,
        world_state: Dict,
        history: Dict
    ) -> PlayabilityMetrics:
        """计算可玩性指标"""

        # 谜题密度: 事件中有多少需要解决的问题
        puzzle_count = len(event_data.get("puzzles", []))
        puzzle_density = min(1.0, puzzle_count / 3.0)  # 3个谜题 = 满分

        # 技能检定多样性: 需要多少种不同的技能/能力
        required_skills = set(event_data.get("required_skills", []))
        skill_variety = min(1.0, len(required_skills) / 5.0)  # 5种技能 = 满分

        # 失败宽容度: 有多少条路径/失败后可以重试
        has_alternative_paths = event_data.get("has_alternatives", False)
        can_retry = event_data.get("allow_retry", True)
        failure_grace = 0.5 if can_retry else 0.3
        if has_alternative_paths:
            failure_grace += 0.3

        # 提示延迟: 当前停滞回合数 (从历史获取)
        stall_turns = history.get("consecutive_stall_turns", 0)
        # 停滞越久，提示延迟越低（越快给提示）
        hint_latency = max(0, 1.0 - stall_turns * 0.3)

        # 防刷抗性: 是否有防止重复刷资源的机制
        has_cooldown = event_data.get("has_cooldown", False)
        has_diminishing_returns = event_data.get("diminishing_returns", False)
        exploit_resistance = 0.4
        if has_cooldown:
            exploit_resistance += 0.3
        if has_diminishing_returns:
            exploit_resistance += 0.3

        # 奖励循环: 奖励是否及时且有意义
        rewards = event_data.get("rewards", {})
        reward_quality = len(rewards) > 0 and any(
            v > 0 for v in rewards.values()
        )
        reward_loop = 0.7 if reward_quality else 0.3

        return PlayabilityMetrics(
            puzzle_density=puzzle_density,
            skill_checks_variety=skill_variety,
            failure_grace=failure_grace,
            hint_latency=hint_latency,
            exploit_resistance=exploit_resistance,
            reward_loop=reward_loop
        )

    def _calculate_narrative(
        self,
        event_data: Dict,
        world_state: Dict,
        history: Dict
    ) -> NarrativeMetrics:
        """计算叙事性指标"""

        # 事件线推进度: 此事件在事件线中的位置
        current_step = event_data.get("arc_step", 0)
        total_steps = event_data.get("arc_total_steps", 1)
        arc_progress = current_step / total_steps if total_steps > 0 else 0

        # 主题回响: 事件是否呼应核心主题
        event_themes = set(event_data.get("themes", []))
        world_themes = set(world_state.get("core_themes", []))
        theme_overlap = len(event_themes & world_themes)
        theme_echo = min(1.0, theme_overlap / 2.0)  # 2个主题重合 = 满分

        # 冲突梯度: 冲突强度是否递增
        previous_tension = history.get("previous_tension", 0.5)
        current_tension = event_data.get("tension_level", 0.5)
        conflict_gradient = min(1.0, max(0, current_tension - previous_tension + 0.5))

        # 伏笔偿还率: 事件是否兑现了之前的伏笔
        payoffs = event_data.get("payoffs", [])
        pending_setups = history.get("pending_setups", [])
        if len(pending_setups) > 0:
            payoff_rate = len(payoffs) / len(pending_setups)
            payoff_debt = min(1.0, payoff_rate)
        else:
            payoff_debt = 0.5  # 没有待偿伏笔，中性分

        # 场景具体性: 场景描述是否具体生动
        scene_description = event_data.get("scene_description", "")
        scene_specificity = min(1.0, len(scene_description) / 200.0)  # 200字 = 满分

        # 节奏平滑度: 与前一事件的节奏差异
        previous_pacing = history.get("previous_pacing", "medium")
        current_pacing = event_data.get("pacing", "medium")
        pacing_map = {"slow": 0.3, "medium": 0.6, "fast": 0.9}
        pacing_diff = abs(pacing_map.get(current_pacing, 0.6) - pacing_map.get(previous_pacing, 0.6))
        pacing_smoothness = 1.0 - pacing_diff  # 差异越小，越平滑

        return NarrativeMetrics(
            arc_progress=arc_progress,
            theme_echo=theme_echo,
            conflict_gradient=conflict_gradient,
            payoff_debt=payoff_debt,
            scene_specificity=scene_specificity,
            pacing_smoothness=pacing_smoothness
        )

    def _calculate_tension_delta(self, event_data: Dict, world_state: Dict) -> float:
        """计算张力变化"""
        current_tension = event_data.get("tension_level", 0.5)
        world_tension = world_state.get("current_tension", 0.5)
        return current_tension - world_tension

    def _calculate_resource_cost(self, event_data: Dict, world_state: Dict) -> float:
        """计算资源消耗（归一化）"""
        costs = event_data.get("resource_costs", {})
        protagonist_resources = world_state.get("protagonist", {}).get("resources", {})

        if not costs:
            return 0.0

        # 计算每项资源的消耗比例
        cost_ratios = []
        for resource, cost in costs.items():
            current = protagonist_resources.get(resource, 1)
            if current > 0:
                ratio = cost / current
                cost_ratios.append(ratio)

        return sum(cost_ratios) / len(cost_ratios) if cost_ratios else 0.0

    def _calculate_stall_risk(
        self,
        event_data: Dict,
        world_state: Dict,
        history: Dict
    ) -> float:
        """计算停滞风险"""

        # 因素1: 难度是否过高
        difficulty = event_data.get("difficulty", 0.5)
        protagonist_power = world_state.get("protagonist", {}).get("power_level", 0.5)
        difficulty_gap = max(0, difficulty - protagonist_power)

        # 因素2: 是否有足够提示
        hint_count = len(event_data.get("hints", []))
        hint_adequacy = min(1.0, hint_count / 2.0)  # 2个提示 = 充足

        # 因素3: 历史停滞情况
        recent_stalls = history.get("recent_stall_count", 0)

        # 综合风险
        stall_risk = (
            difficulty_gap * 0.4 +
            (1 - hint_adequacy) * 0.3 +
            min(1.0, recent_stalls * 0.3)
        )

        return min(1.0, stall_risk)


# ============================================================================
# 动态权重调节器
# ============================================================================

class DynamicWeightAdjuster:
    """动态权重调节器（根据游戏状态调整评分权重）"""

    def __init__(
        self,
        base_playability_weight: float = 0.6,
        base_narrative_weight: float = 0.4
    ):
        self.base_playability = base_playability_weight
        self.base_narrative = base_narrative_weight

    def adjust_weights(
        self,
        history: Dict,
        pending_setups: List
    ) -> tuple[float, float]:
        """根据当前状态动态调整权重"""

        playability_weight = self.base_playability
        narrative_weight = self.base_narrative

        # 规则1: 停滞≥2回合 → 提高可玩性权重（降低难度，增加提示）
        stall_turns = history.get("consecutive_stall_turns", 0)
        if stall_turns >= 2:
            playability_weight += 0.15
            narrative_weight -= 0.15

        # 规则2: 伏笔临期 → 提高叙事权重（优先兑现伏笔）
        overdue_setups = [s for s in pending_setups if s.get("is_overdue", False)]
        if len(overdue_setups) > 0:
            narrative_weight += 0.2
            playability_weight -= 0.2

        # 规则3: 张力过低 → 提高叙事权重（推进剧情）
        current_tension = history.get("current_tension", 0.5)
        if current_tension < 0.3:
            narrative_weight += 0.1
            playability_weight -= 0.1

        # 归一化
        total = playability_weight + narrative_weight
        playability_weight /= total
        narrative_weight /= total

        return playability_weight, narrative_weight
