"""动作队列数据模型"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class ActionType(Enum):
    """动作类型"""
    SCENE = "scene"  # 场景描述
    INTERACTION = "interaction"  # 交互/选择
    CHECK = "check"  # 技能检定/判定
    TOOL = "tool"  # 工具调用（查询/搜索等）
    OUTCOME = "outcome"  # 结果分支
    NARRATION = "narration"  # 旁白/叙述


class HintType(Enum):
    """提示类型"""
    IMPLICIT = "implicit"  # 隐性提示（环境暗示）
    EXPLICIT = "explicit"  # 显性提示（直接指向）
    RED_HERRING = "red_herring"  # 红鲱鱼（误导）


@dataclass
class ActionStep:
    """动作步骤"""
    type: ActionType
    spec: str  # 具体说明
    params: Dict[str, Any] = field(default_factory=dict)

    # 可选：检定要求
    requires: List[str] = field(default_factory=list)  # 能力/资源要求

    # 可选：分支
    branches: Dict[str, Any] = field(default_factory=dict)  # success/partial/fail


@dataclass
class Hint:
    """提示"""
    kind: HintType
    trigger: str  # 触发条件
    text: str
    evidence_id: Optional[str] = None  # 关联的证据ID


@dataclass
class ActionQueue:
    """动作队列（一幕的具体执行）"""
    event_id: str
    goal: str  # 本幕目标

    # 步骤序列
    steps: List[ActionStep] = field(default_factory=list)

    # 提示槽位
    hints: List[Hint] = field(default_factory=list)

    # 状态补丁模板
    state_patch_schema: Dict[str, Any] = field(default_factory=dict)

    # 执行结果（运行时填充）
    execution_result: Optional[Dict[str, Any]] = None
    success: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionQueue":
        """从字典创建"""
        steps = [
            ActionStep(
                type=ActionType(s["type"]),
                spec=s["spec"],
                params=s.get("params", {}),
                requires=s.get("requires", []),
                branches=s.get("branches", {})
            )
            for s in data.get("steps", [])
        ]

        hints = [
            Hint(
                kind=HintType(h["kind"]),
                trigger=h["trigger"],
                text=h["text"],
                evidence_id=h.get("evidence_id")
            )
            for h in data.get("hints", [])
        ]

        return cls(
            event_id=data["event_id"],
            goal=data["goal"],
            steps=steps,
            hints=hints,
            state_patch_schema=data.get("state_patch_schema", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "goal": self.goal,
            "steps": [
                {
                    "type": s.type.value,
                    "spec": s.spec,
                    "params": s.params,
                    "requires": s.requires,
                    "branches": s.branches
                }
                for s in self.steps
            ],
            "hints": [
                {
                    "kind": h.kind.value,
                    "trigger": h.trigger,
                    "text": h.text,
                    "evidence_id": h.evidence_id
                }
                for h in self.hints
            ],
            "state_patch_schema": self.state_patch_schema,
            "execution_result": self.execution_result,
            "success": self.success
        }
