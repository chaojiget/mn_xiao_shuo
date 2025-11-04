"""一致性审计系统

根据 TECHNICAL_IMPLEMENTATION_PLAN.md Section 2.4 设计
检查五大类一致性：硬规则、因果、资源、角色、时间线
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from ..models.world_state import WorldState, Character
from ..models.event_node import EventNode


class ViolationType(Enum):
    """违规类型"""
    HARD_RULE = "hard_rule"          # 硬规则违规
    CAUSALITY = "causality"          # 因果违规
    RESOURCE = "resource"            # 资源违规
    CHARACTER = "character"          # 角色违规
    TIMELINE = "timeline"            # 时间线违规
    POWER_SCALING = "power_scaling"  # 力量体系违规


class ViolationSeverity(Enum):
    """违规严重性"""
    CRITICAL = "critical"  # 致命违规，必须修复
    HIGH = "high"         # 高优先级
    MEDIUM = "medium"     # 中优先级
    LOW = "low"          # 低优先级


@dataclass
class ConsistencyViolation:
    """一致性违规记录"""
    type: ViolationType
    severity: ViolationSeverity
    description: str
    affected_entities: List[str]
    suggested_fix: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditReport:
    """审计报告"""
    violations: List[ConsistencyViolation]
    passed: bool
    summary: str
    recommendations: List[str]
    timestamp: int = 0
    turn: int = 0


class ConsistencyAuditor:
    """一致性审计器

    检查世界状态和事件的一致性，防止逻辑错误和矛盾
    """

    def __init__(self, setting: Dict[str, Any] = None):
        """初始化审计器

        Args:
            setting: 小说设定（包含硬规则、力量体系等）
        """
        self.setting = setting or {}
        self.violation_history: List[ConsistencyViolation] = []

        # 从设定中提取硬规则
        self.hard_rules = self._extract_hard_rules()

    def _extract_hard_rules(self) -> Dict[str, Any]:
        """从设定中提取硬规则"""
        rules = {}

        # 科幻类型的硬规则示例
        if self.setting.get("类型") == "科幻":
            rules["max_speed"] = "光速"
            rules["ftl_method"] = self.setting.get("FTL方式", "未定义")

        # 玄幻类型的硬规则示例
        elif self.setting.get("类型") in ["玄幻", "仙侠"]:
            rules["power_system"] = self.setting.get("修炼体系", {})
            rules["cultivation_levels"] = self.setting.get("境界划分", [])

        return rules

    def audit_world_state(
        self,
        world_state: WorldState,
        event: Optional[EventNode] = None
    ) -> AuditReport:
        """审计世界状态

        Args:
            world_state: 当前世界状态
            event: 触发审计的事件（可选）

        Returns:
            AuditReport: 审计报告
        """
        violations = []

        # 1. 硬规则检查
        violations.extend(self._check_hard_rules(world_state, event))

        # 2. 资源一致性检查
        violations.extend(self._check_resources(world_state))

        # 3. 角色一致性检查
        violations.extend(self._check_characters(world_state))

        # 4. 因果一致性检查
        if event:
            violations.extend(self._check_causality(world_state, event))

        # 5. 时间线一致性检查
        violations.extend(self._check_timeline(world_state))

        # 6. 力量体系检查（玄幻/仙侠特有）
        if self.setting.get("类型") in ["玄幻", "仙侠"]:
            violations.extend(self._check_power_scaling(world_state))

        # 记录历史
        self.violation_history.extend(violations)

        # 生成报告
        return self._generate_report(violations, world_state)

    def _check_hard_rules(
        self,
        world_state: WorldState,
        event: Optional[EventNode]
    ) -> List[ConsistencyViolation]:
        """检查硬规则违规"""
        violations = []

        # 示例：检查FTL方式是否被违反
        if "ftl_method" in self.hard_rules:
            ftl_method = self.hard_rules["ftl_method"]
            # 这里可以检查事件描述中是否使用了不符合设定的FTL方式
            # 实际实现需要更复杂的NLP分析
            pass

        return violations

    def _check_resources(self, world_state: WorldState) -> List[ConsistencyViolation]:
        """检查资源一致性"""
        violations = []

        # 检查资源不能为负
        for res_type, resource in world_state.resources.items():
            if resource.amount < 0:
                violations.append(ConsistencyViolation(
                    type=ViolationType.RESOURCE,
                    severity=ViolationSeverity.CRITICAL,
                    description=f"资源 '{res_type}' 数量为负数: {resource.amount}",
                    affected_entities=[res_type],
                    suggested_fix=f"将 {res_type} 设置为 0 或检查消耗逻辑"
                ))

            # 检查是否超过上限
            if resource.max_capacity and resource.amount > resource.max_capacity:
                violations.append(ConsistencyViolation(
                    type=ViolationType.RESOURCE,
                    severity=ViolationSeverity.HIGH,
                    description=f"资源 '{res_type}' 超过上限: {resource.amount}/{resource.max_capacity}",
                    affected_entities=[res_type],
                    suggested_fix=f"将 {res_type} 限制在 {resource.max_capacity} 以内"
                ))

        return violations

    def _check_characters(self, world_state: WorldState) -> List[ConsistencyViolation]:
        """检查角色一致性"""
        violations = []

        for char_id, char in world_state.characters.items():
            # 检查角色位置是否有效
            if char.location and char.location not in world_state.locations:
                violations.append(ConsistencyViolation(
                    type=ViolationType.CHARACTER,
                    severity=ViolationSeverity.HIGH,
                    description=f"角色 '{char.name}' 位于不存在的地点: {char.location}",
                    affected_entities=[char_id, char.location],
                    suggested_fix=f"更新角色位置或添加地点定义"
                ))

            # 检查关系网络完整性
            for related_char_id in char.relationships.keys():
                if related_char_id not in world_state.characters:
                    violations.append(ConsistencyViolation(
                        type=ViolationType.CHARACTER,
                        severity=ViolationSeverity.MEDIUM,
                        description=f"角色 '{char.name}' 与不存在的角色有关系: {related_char_id}",
                        affected_entities=[char_id, related_char_id],
                        suggested_fix="移除无效关系或添加角色定义"
                    ))

            # 检查角色资源
            for res_type, amount in char.resources.items():
                if amount < 0:
                    violations.append(ConsistencyViolation(
                        type=ViolationType.RESOURCE,
                        severity=ViolationSeverity.CRITICAL,
                        description=f"角色 '{char.name}' 的资源 '{res_type}' 为负数: {amount}",
                        affected_entities=[char_id, res_type],
                        suggested_fix="重新计算资源或检查消耗逻辑"
                    ))

        return violations

    def _check_causality(
        self,
        world_state: WorldState,
        event: EventNode
    ) -> List[ConsistencyViolation]:
        """检查因果一致性"""
        violations = []

        # 检查前置条件是否满足
        # 注意：这里假设 completed_events 在 world_state.events_log 中
        completed_event_ids = [
            e.get("event_id") for e in world_state.events_log
            if e.get("status") == "completed"
        ]

        for prereq_id in event.prerequisites:
            if prereq_id not in completed_event_ids:
                violations.append(ConsistencyViolation(
                    type=ViolationType.CAUSALITY,
                    severity=ViolationSeverity.CRITICAL,
                    description=f"事件 '{event.title}' 的前置事件 '{prereq_id}' 未完成",
                    affected_entities=[event.id, prereq_id],
                    suggested_fix=f"先完成前置事件或移除前置条件"
                ))

        # 检查必需标志位
        for flag, required_value in event.required_flags.items():
            current_value = world_state.flags.get(flag)
            if current_value != required_value:
                violations.append(ConsistencyViolation(
                    type=ViolationType.CAUSALITY,
                    severity=ViolationSeverity.HIGH,
                    description=f"事件 '{event.title}' 需要标志 '{flag}' 为 {required_value}，实际为 {current_value}",
                    affected_entities=[event.id],
                    suggested_fix=f"设置标志 {flag} = {required_value}"
                ))

        return violations

    def _check_timeline(self, world_state: WorldState) -> List[ConsistencyViolation]:
        """检查时间线一致性"""
        violations = []

        # 检查时间戳单调递增
        if len(world_state.events_log) >= 2:
            for i in range(len(world_state.events_log) - 1):
                current_ts = world_state.events_log[i].get("timestamp", 0)
                next_ts = world_state.events_log[i + 1].get("timestamp", 0)

                if next_ts < current_ts:
                    violations.append(ConsistencyViolation(
                        type=ViolationType.TIMELINE,
                        severity=ViolationSeverity.MEDIUM,
                        description=f"时间线倒退: 事件 {i} ({current_ts}) -> 事件 {i+1} ({next_ts})",
                        affected_entities=[f"event_{i}", f"event_{i+1}"],
                        suggested_fix="修正时间戳顺序"
                    ))

        return violations

    def _check_power_scaling(self, world_state: WorldState) -> List[ConsistencyViolation]:
        """检查力量体系一致性（玄幻/仙侠）"""
        violations = []

        cultivation_levels = self.hard_rules.get("cultivation_levels", [])
        if not cultivation_levels:
            return violations

        # 检查主角的境界变化是否合理
        protagonist = world_state.get_protagonist()
        if not protagonist:
            return violations

        current_level = protagonist.attributes.get("cultivation_level", 0)

        # 检查境界是否在有效范围内
        if current_level < 0 or current_level >= len(cultivation_levels):
            violations.append(ConsistencyViolation(
                type=ViolationType.POWER_SCALING,
                severity=ViolationSeverity.HIGH,
                description=f"主角境界超出范围: {current_level}/{len(cultivation_levels)-1}",
                affected_entities=[protagonist.id],
                suggested_fix="调整境界到有效范围"
            ))

        # 可以添加更多力量体系检查，例如：
        # - 检查境界与战力是否匹配
        # - 检查修炼速度是否合理
        # - 检查资源消耗与境界提升的对应关系

        return violations

    def _generate_report(
        self,
        violations: List[ConsistencyViolation],
        world_state: WorldState
    ) -> AuditReport:
        """生成审计报告"""
        # 统计严重违规
        critical = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
        high = [v for v in violations if v.severity == ViolationSeverity.HIGH]

        # 判断是否通过
        passed = len(critical) == 0

        # 生成摘要
        if passed:
            if len(violations) == 0:
                summary = "完美通过，无任何违规"
            else:
                summary = f"通过（{len(violations)} 个低优先级问题）"
        else:
            summary = f"失败（{len(critical)} 个致命违规，{len(high)} 个高优先级违规）"

        # 生成建议
        recommendations = []

        if critical:
            recommendations.append(f"立即修复 {len(critical)} 个致命违规")

        if high:
            recommendations.append(f"优先处理 {len(high)} 个高优先级违规")

        # 检查重复违规模式
        violation_types = [v.type for v in violations]
        from collections import Counter
        type_counts = Counter(violation_types)

        for vtype, count in type_counts.most_common(3):
            if count >= 3:
                recommendations.append(
                    f"注意：{vtype.value} 类型违规出现 {count} 次，可能存在系统性问题"
                )

        return AuditReport(
            violations=violations,
            passed=passed,
            summary=summary,
            recommendations=recommendations,
            timestamp=world_state.timestamp,
            turn=world_state.turn
        )

    def get_violation_stats(self) -> Dict[str, int]:
        """获取历史违规统计"""
        stats = {
            "total": len(self.violation_history),
            "by_type": {},
            "by_severity": {}
        }

        for v in self.violation_history:
            # 按类型统计
            type_key = v.type.value
            stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1

            # 按严重性统计
            severity_key = v.severity.value
            stats["by_severity"][severity_key] = stats["by_severity"].get(severity_key, 0) + 1

        return stats
