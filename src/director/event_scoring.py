"""事件线评分系统

根据 TECHNICAL_IMPLEMENTATION_PLAN.md Section 2.3 设计
支持三种评分模式：可玩性优先、叙事优先、混合模式
"""

from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

from ..models.event_node import EventNode, EventArc


class ScoringMode(Enum):
    """评分模式"""
    PLAYABILITY = "playability"  # 可玩性优先
    NARRATIVE = "narrative"      # 叙事优先
    HYBRID = "hybrid"            # 混合模式


@dataclass
class EventScore:
    """事件评分结果"""
    event_id: str
    total_score: float
    playability_score: float
    narrative_score: float
    genre_score: float  # 类型特定评分

    # 分项评分
    sub_scores: Dict[str, float]

    # 评分说明
    reasoning: str = ""


class EventScorer:
    """事件评分器

    根据不同的评分模式计算事件的优先级分数
    """

    def __init__(
        self,
        mode: ScoringMode = ScoringMode.HYBRID,
        genre: str = "scifi",  # scifi 或 xianxia
        weights: Optional[Dict[str, float]] = None
    ):
        """初始化评分器

        Args:
            mode: 评分模式
            genre: 小说类型
            weights: 自定义权重配置
        """
        self.mode = mode
        self.genre = genre
        self.weights = weights or self._get_default_weights()

    def _get_default_weights(self) -> Dict[str, float]:
        """获取默认权重配置"""
        if self.mode == ScoringMode.PLAYABILITY:
            return {
                "playability": 0.7,
                "narrative": 0.2,
                "genre": 0.1
            }
        elif self.mode == ScoringMode.NARRATIVE:
            return {
                "playability": 0.2,
                "narrative": 0.7,
                "genre": 0.1
            }
        else:  # HYBRID
            return {
                "playability": 0.4,
                "narrative": 0.4,
                "genre": 0.2
            }

    def score_event(self, event: EventNode, context: Dict = None) -> EventScore:
        """评分单个事件

        Args:
            event: 事件节点
            context: 上下文信息（当前状态、已完成事件等）

        Returns:
            EventScore: 评分结果
        """
        context = context or {}

        # 计算各项评分
        playability_score = self._score_playability(event, context)
        narrative_score = self._score_narrative(event, context)
        genre_score = self._score_genre(event, context)

        # 加权总分
        total_score = (
            playability_score * self.weights["playability"] +
            narrative_score * self.weights["narrative"] +
            genre_score * self.weights["genre"]
        )

        # 收集分项评分
        sub_scores = {
            "playability": playability_score,
            "narrative": narrative_score,
            "genre": genre_score
        }

        # 生成评分说明
        reasoning = self._generate_reasoning(event, sub_scores)

        return EventScore(
            event_id=event.id,
            total_score=total_score,
            playability_score=playability_score,
            narrative_score=narrative_score,
            genre_score=genre_score,
            sub_scores=sub_scores,
            reasoning=reasoning
        )

    def _score_playability(self, event: EventNode, context: Dict) -> float:
        """计算可玩性评分 (0-100)

        可玩性指标：
        - puzzle_density: 谜题密度
        - skill_checks_variety: 检定多样性
        - failure_grace: 失败容错度
        - hint_latency: 提示延迟
        - exploit_resistance: 抗刷分
        - reward_loop: 奖励循环
        """
        scores = []

        # 1. 谜题密度 (0-1) -> 0-20分
        if event.puzzle_density > 0:
            scores.append(min(event.puzzle_density * 20, 20))

        # 2. 检定多样性 (0-1) -> 0-20分
        if event.skill_checks_variety > 0:
            scores.append(min(event.skill_checks_variety * 20, 20))

        # 3. 失败容错度 (0-1) -> 0-15分
        if event.failure_grace > 0:
            scores.append(min(event.failure_grace * 15, 15))

        # 4. 提示延迟 (0-1, 值越高提示越晚 -> 难度越高) -> 0-15分
        if event.hint_latency > 0:
            scores.append(min(event.hint_latency * 15, 15))

        # 5. 抗刷分 (0-1) -> 0-15分
        if event.exploit_resistance > 0:
            scores.append(min(event.exploit_resistance * 15, 15))

        # 6. 奖励循环 (0-1) -> 0-15分
        if event.reward_loop > 0:
            scores.append(min(event.reward_loop * 15, 15))

        # 如果没有任何可玩性指标，返回基础分
        if not scores:
            return 30.0  # 基础分

        return sum(scores)

    def _score_narrative(self, event: EventNode, context: Dict) -> float:
        """计算叙事评分 (0-100)

        叙事指标：
        - arc_progress: 事件线推进
        - theme_echo: 主题共鸣
        - conflict_gradient: 冲突梯度
        - payoff_debt: 伏笔偿还
        - scene_specificity: 场景具体性
        - pacing_smoothness: 节奏流畅度
        """
        scores = []

        # 1. 事件线推进 (0-1) -> 0-25分
        if event.arc_progress > 0:
            scores.append(min(event.arc_progress * 25, 25))

        # 2. 主题共鸣 (0-1) -> 0-20分
        if event.theme_echo > 0:
            scores.append(min(event.theme_echo * 20, 20))

        # 3. 冲突梯度 (0-1) -> 0-20分
        if event.conflict_gradient > 0:
            scores.append(min(event.conflict_gradient * 20, 20))

        # 4. 伏笔偿还 (0-1) -> 0-15分
        # 偿还伏笔很重要，给予奖励
        if event.payoff_debt > 0:
            scores.append(min(event.payoff_debt * 15, 15))

        # 5. 场景具体性 (0-1) -> 0-10分
        if event.scene_specificity > 0:
            scores.append(min(event.scene_specificity * 10, 10))

        # 6. 节奏流畅度 (0-1) -> 0-10分
        if event.pacing_smoothness > 0:
            scores.append(min(event.pacing_smoothness * 10, 10))

        # 如果没有任何叙事指标，返回基础分
        if not scores:
            return 30.0  # 基础分

        return sum(scores)

    def _score_genre(self, event: EventNode, context: Dict) -> float:
        """计算类型特定评分 (0-100)

        玄幻/仙侠特定指标：
        - upgrade_frequency: 升级频率
        - resource_gain: 资源获取
        - combat_variety: 战斗多样性
        - reversal_satisfaction: 逆袭爽感
        - faction_expansion: 势力扩张
        """
        if self.genre == "xianxia":
            return self._score_xianxia(event, context)
        else:
            return self._score_scifi(event, context)

    def _score_xianxia(self, event: EventNode, context: Dict) -> float:
        """玄幻/仙侠类型评分"""
        scores = []

        # 1. 升级频率 (0-1) -> 0-25分
        if event.upgrade_frequency > 0:
            scores.append(min(event.upgrade_frequency * 25, 25))

        # 2. 资源获取 (0-1) -> 0-25分
        if event.resource_gain > 0:
            scores.append(min(event.resource_gain * 25, 25))

        # 3. 战斗多样性 (0-1) -> 0-20分
        if event.combat_variety > 0:
            scores.append(min(event.combat_variety * 20, 20))

        # 4. 逆袭爽感 (0-1) -> 0-20分
        if event.reversal_satisfaction > 0:
            scores.append(min(event.reversal_satisfaction * 20, 20))

        # 5. 势力扩张 (0-1) -> 0-10分
        if event.faction_expansion > 0:
            scores.append(min(event.faction_expansion * 10, 10))

        if not scores:
            return 40.0  # 基础分

        return sum(scores)

    def _score_scifi(self, event: EventNode, context: Dict) -> float:
        """科幻类型评分"""
        # 科幻类型暂时使用简化评分
        # 可以根据具体需求添加科幻特定指标
        scores = []

        # 使用通用的张力增量作为科幻评分参考
        if event.tension_delta > 0:
            scores.append(min(event.tension_delta * 50, 50))

        # 检查是否有技术/科学相关的标签
        tech_tags = ["technology", "science", "exploration", "mystery"]
        tech_score = sum(10 for tag in event.tags if tag in tech_tags)
        if tech_score > 0:
            scores.append(min(tech_score, 30))

        if not scores:
            return 40.0  # 基础分

        return sum(scores)

    def _generate_reasoning(self, event: EventNode, sub_scores: Dict[str, float]) -> str:
        """生成评分说明"""
        reasons = []

        # 可玩性评分说明
        p_score = sub_scores["playability"]
        if p_score >= 80:
            reasons.append("可玩性极高（谜题丰富、检定多样）")
        elif p_score >= 60:
            reasons.append("可玩性良好")
        elif p_score < 40:
            reasons.append("可玩性偏低（建议增加互动元素）")

        # 叙事评分说明
        n_score = sub_scores["narrative"]
        if n_score >= 80:
            reasons.append("叙事优秀（推进剧情、主题共鸣强）")
        elif n_score >= 60:
            reasons.append("叙事良好")
        elif n_score < 40:
            reasons.append("叙事偏弱（建议加强剧情关联）")

        # 类型评分说明
        g_score = sub_scores["genre"]
        if self.genre == "xianxia":
            if g_score >= 70:
                reasons.append("爽文要素充足（升级/资源/逆袭）")
            elif g_score < 50:
                reasons.append("爽文要素不足")

        return "; ".join(reasons) if reasons else "标准事件"

    def rank_events(
        self,
        events: List[EventNode],
        context: Dict = None,
        top_k: int = None
    ) -> List[tuple[EventNode, EventScore]]:
        """对多个事件进行评分和排序

        Args:
            events: 事件列表
            context: 上下文
            top_k: 返回前k个，None返回全部

        Returns:
            List of (event, score) tuples, sorted by score descending
        """
        scored_events = [
            (event, self.score_event(event, context))
            for event in events
        ]

        # 按总分降序排序
        scored_events.sort(key=lambda x: x[1].total_score, reverse=True)

        if top_k:
            return scored_events[:top_k]

        return scored_events

    def score_arc(self, arc: EventArc, context: Dict = None) -> float:
        """评估整个事件线的分数

        返回事件线所有事件的平均分
        """
        if not arc.events:
            return 0.0

        total_score = 0.0
        for event in arc.events:
            score = self.score_event(event, context)
            total_score += score.total_score

        return total_score / len(arc.events)
