"""
一致性审计系统
Consistency Auditor

检查:
1. 硬规则 (Hard Rules) - 世界设定的物理/魔法规则
2. 因果一致性 (Causality) - 事件的前因后果
3. 资源守恒 (Resource Conservation) - 资源不能凭空产生
4. 角色一致性 (Character Consistency) - 角色行为符合设定
5. 时间线一致性 (Timeline) - 时间顺序合理
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal, Any
from dataclasses import dataclass


# ============================================================================
# 审计结果
# ============================================================================

@dataclass
class AuditIssue:
    """审计问题"""
    severity: Literal["critical", "high", "medium", "low"]
    category: Literal["hard_rule", "causality", "resource", "character", "timeline", "theme"]
    description: str
    location: str  # 问题位置，如 "chapter_5:paragraph_3"
    suggestion: Optional[str] = None  # 修复建议


class AuditReport(BaseModel):
    """审计报告"""
    passed: bool = True
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # 统计
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    def add_issue(self, issue: AuditIssue):
        """添加问题"""
        self.issues.append({
            "severity": issue.severity,
            "category": issue.category,
            "description": issue.description,
            "location": issue.location,
            "suggestion": issue.suggestion
        })

        # 更新统计
        if issue.severity == "critical":
            self.critical_count += 1
            self.passed = False
        elif issue.severity == "high":
            self.high_count += 1
            self.passed = False
        elif issue.severity == "medium":
            self.medium_count += 1
        else:
            self.low_count += 1

    def add_warning(self, message: str):
        """添加警告"""
        self.warnings.append(message)


# ============================================================================
# 一致性审计器
# ============================================================================

class ConsistencyAuditor:
    """一致性审计器"""

    def __init__(self, hard_rules: List[str], soft_rules: Optional[List[str]] = None):
        self.hard_rules = hard_rules
        self.soft_rules = soft_rules or []

    def audit_content(
        self,
        content: str,
        world_state: Dict[str, Any],
        history: Dict[str, Any],
        content_type: Literal["chapter", "event", "dialogue"] = "chapter"
    ) -> AuditReport:
        """审计内容"""

        report = AuditReport()

        # 1. 硬规则检查
        self._check_hard_rules(content, world_state, report)

        # 2. 因果一致性检查
        self._check_causality(content, history, report)

        # 3. 资源守恒检查
        self._check_resource_conservation(content, world_state, report)

        # 4. 角色一致性检查
        self._check_character_consistency(content, world_state, report)

        # 5. 时间线一致性检查
        self._check_timeline(content, history, report)

        # 6. 主题一致性检查(软规则)
        self._check_theme_consistency(content, world_state, report)

        return report

    def _check_hard_rules(
        self,
        content: str,
        world_state: Dict[str, Any],
        report: AuditReport
    ):
        """检查硬规则"""

        # 遍历所有硬规则，检查是否违反
        for rule in self.hard_rules:
            rule_lower = rule.lower()

            # 示例规则检查
            if "能量守恒" in rule or "资源守恒" in rule:
                # 检查是否有"凭空出现"的描述
                forbidden_patterns = [
                    "凭空出现", "突然出现", "无中生有",
                    "without reason", "out of nowhere"
                ]
                for pattern in forbidden_patterns:
                    if pattern in content.lower():
                        report.add_issue(AuditIssue(
                            severity="critical",
                            category="hard_rule",
                            description=f"违反硬规则'{rule}': 发现'{pattern}'",
                            location="content",
                            suggestion="为资源/能量的来源提供合理解释"
                        ))

            elif "禁止读心" in rule or "no mind reading" in rule_lower:
                # 检查是否有主角直接知道他人想法的描述
                mind_reading_patterns = [
                    "他想", "她想", "对方心想", "内心", "暗自思量",
                    "he thought", "she thought", "thinking"
                ]
                # 排除合理的情况：对话、猜测
                if any(p in content for p in mind_reading_patterns):
                    if "猜测" not in content and "推测" not in content and "可能" not in content:
                        report.add_warning(
                            f"可能违反硬规则'{rule}': 检测到可能的读心描述，请确认"
                        )

            elif "因果" in rule or "causality" in rule_lower:
                # 检查是否有无因果的突变
                sudden_change_patterns = [
                    "突然间", "瞬间", "毫无征兆", "without warning",
                    "out of nowhere", "突然就"
                ]
                for pattern in sudden_change_patterns:
                    if pattern in content:
                        report.add_issue(AuditIssue(
                            severity="medium",
                            category="hard_rule",
                            description=f"可能违反因果规则: 发现'{pattern}'",
                            location="content",
                            suggestion="为突变提供铺垫或解释"
                        ))

    def _check_causality(
        self,
        content: str,
        history: Dict[str, Any],
        report: AuditReport
    ):
        """检查因果一致性"""

        # 检查事件前置条件
        prerequisites = history.get("required_prerequisites", [])
        completed_events = history.get("completed_events", [])

        for prereq in prerequisites:
            if prereq not in completed_events:
                report.add_issue(AuditIssue(
                    severity="high",
                    category="causality",
                    description=f"缺少前置事件: {prereq}",
                    location="event_flow",
                    suggestion=f"先完成事件 {prereq} 或移除此前置条件"
                ))

        # 检查是否引用了不存在的事件/角色
        mentioned_characters = history.get("mentioned_characters", [])
        existing_characters = history.get("existing_characters", [])

        for char in mentioned_characters:
            if char not in existing_characters:
                report.add_issue(AuditIssue(
                    severity="high",
                    category="causality",
                    description=f"引用了未定义的角色: {char}",
                    location="content",
                    suggestion=f"先引入角色 {char} 或移除引用"
                ))

    def _check_resource_conservation(
        self,
        content: str,
        world_state: Dict[str, Any],
        report: AuditReport
    ):
        """检查资源守恒"""

        # 获取主角当前资源
        protagonist = world_state.get("protagonist", {})
        current_resources = protagonist.get("resources", {})

        # 检查内容中是否有资源消耗描述
        resource_changes = self._extract_resource_changes(content)

        for resource, delta in resource_changes.items():
            current = current_resources.get(resource, 0)

            # 检查资源减少是否合理
            if delta < 0 and abs(delta) > current:
                report.add_issue(AuditIssue(
                    severity="critical",
                    category="resource",
                    description=f"资源不足: {resource} 当前={current}, 消耗={abs(delta)}",
                    location="content",
                    suggestion=f"减少 {resource} 的消耗或增加角色的初始资源"
                ))

            # 检查资源增加是否有来源
            if delta > 0:
                has_source = any(
                    keyword in content
                    for keyword in ["获得", "奖励", "拾取", "找到", "earned", "found", "gained"]
                )
                if not has_source:
                    report.add_warning(
                        f"资源增加 {resource}+{delta} 但未明确来源"
                    )

    def _extract_resource_changes(self, content: str) -> Dict[str, float]:
        """从内容中提取资源变化（简化版本）"""
        # TODO: 实现更复杂的NLP解析
        # 这里返回空字典作为占位
        return {}

    def _check_character_consistency(
        self,
        content: str,
        world_state: Dict[str, Any],
        report: AuditReport
    ):
        """检查角色一致性"""

        # 获取角色设定
        characters = world_state.get("characters", {})

        for char_id, char_data in characters.items():
            char_name = char_data.get("name", "")
            personality = char_data.get("personality", [])

            # 检查角色是否在内容中出现
            if char_name not in content:
                continue

            # 检查行为是否与性格一致
            # 例如：性格中有"正直"但内容中有"欺骗"行为
            if "正直" in personality or "诚实" in personality:
                dishonest_actions = ["欺骗", "撒谎", "隐瞒", "lie", "deceive"]
                for action in dishonest_actions:
                    if action in content and char_name in content:
                        # 检查上下文，是否有合理解释
                        if "迫不得已" not in content and "不得不" not in content:
                            report.add_issue(AuditIssue(
                                severity="medium",
                                category="character",
                                description=f"角色 {char_name} 的行为与性格 '{personality}' 不一致",
                                location="content",
                                suggestion="为角色的反常行为提供合理动机"
                            ))

    def _check_timeline(
        self,
        content: str,
        history: Dict[str, Any],
        report: AuditReport
    ):
        """检查时间线一致性"""

        # 检查时间顺序
        current_turn = history.get("current_turn", 0)
        previous_turn = history.get("previous_turn", 0)

        if current_turn < previous_turn:
            report.add_issue(AuditIssue(
                severity="critical",
                category="timeline",
                description=f"时间倒流: 当前回合{current_turn} < 上一回合{previous_turn}",
                location="metadata",
                suggestion="修正回合数"
            ))

        # 检查事件发生的时间间隔
        # 例如：不能在1天内完成需要1个月的任务
        time_keywords = {
            "瞬间": 0.001,
            "几分钟": 0.003,
            "几小时": 0.1,
            "一天": 1,
            "几天": 3,
            "一周": 7,
            "一个月": 30,
            "几个月": 90,
            "一年": 365
        }

        estimated_time = 1  # 默认1天
        for keyword, days in time_keywords.items():
            if keyword in content:
                estimated_time = days
                break

        # 如果内容暗示需要很长时间，但章节间隔很短
        chapter_gap = current_turn - previous_turn
        if estimated_time > 7 and chapter_gap < 3:
            report.add_warning(
                f"时间线可能不一致: 内容暗示需要 {estimated_time} 天，但只过了 {chapter_gap} 章"
            )

    def _check_theme_consistency(
        self,
        content: str,
        world_state: Dict[str, Any],
        report: AuditReport
    ):
        """检查主题一致性（软规则）"""

        core_themes = world_state.get("core_themes", [])

        if not core_themes:
            return

        # 检查内容是否与核心主题相关
        theme_mentioned = any(theme in content for theme in core_themes)

        if not theme_mentioned:
            report.add_warning(
                f"内容未体现核心主题: {', '.join(core_themes)}"
            )


# ============================================================================
# 自动修复建议生成器
# ============================================================================

class AutoFixer:
    """自动修复建议生成器"""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    async def suggest_fixes(
        self,
        content: str,
        audit_report: AuditReport
    ) -> Dict[str, str]:
        """为审计问题生成修复建议"""

        if audit_report.passed:
            return {"status": "passed", "message": "无需修复"}

        # 构建修复提示词
        issues_text = "\n".join([
            f"{i+1}. [{issue['severity']}] {issue['category']}: {issue['description']}"
            for i, issue in enumerate(audit_report.issues)
        ])

        prompt = f"""你是一个小说内容审计助手。以下内容存在一致性问题，请提供修复建议。

## 原始内容
{content[:500]}...

## 发现的问题
{issues_text}

请针对每个问题提供具体的修复建议：
1. 指出需要修改的具体位置
2. 建议如何修改
3. 修改后的示例文本

输出JSON格式：
{{
  "fixes": [
    {{
      "issue_index": 0,
      "fix_description": "...",
      "suggested_text": "..."
    }}
  ],
  "rewrite_suggestion": "是否建议重写整段内容 (true/false)"
}}
"""

        try:
            response = await self.llm_client.generate_structured(
                prompt=prompt,
                response_schema={
                    "type": "object",
                    "properties": {
                        "fixes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "issue_index": {"type": "integer"},
                                    "fix_description": {"type": "string"},
                                    "suggested_text": {"type": "string"}
                                }
                            }
                        },
                        "rewrite_suggestion": {"type": "boolean"}
                    }
                }
            )
            return response
        except Exception:
            return {
                "fixes": [],
                "rewrite_suggestion": audit_report.critical_count > 0
            }
