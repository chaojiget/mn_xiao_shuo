"""任务系统数据模型

Phase 2 - 任务系统实现
定义任务相关的数据结构：Quest, QuestObjective, QuestReward
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QuestType(str, Enum):
    """任务类型"""

    MAIN = "main"  # 主线任务
    SIDE = "side"  # 支线任务
    HIDDEN = "hidden"  # 隐藏任务


class QuestStatus(str, Enum):
    """任务状态"""

    AVAILABLE = "available"  # 可接取
    ACTIVE = "active"  # 进行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class ObjectiveType(str, Enum):
    """任务目标类型"""

    EXPLORE = "explore"  # 探索地点
    COLLECT = "collect"  # 收集物品
    DEFEAT = "defeat"  # 击败敌人
    TALK = "talk"  # 对话
    REACH = "reach"  # 到达地点


class QuestObjective(BaseModel):
    """任务目标

    单个任务可以有多个目标
    """

    id: str
    type: ObjectiveType
    description: str
    target: str  # location_id, item_id, npc_id, enemy_id
    current: int = 0
    required: int = 1
    completed: bool = False

    def update_progress(self, amount: int = 1) -> bool:
        """更新进度

        Args:
            amount: 进度增加量

        Returns:
            是否完成目标
        """
        self.current = min(self.current + amount, self.required)
        self.completed = self.current >= self.required
        return self.completed

    def get_progress_percent(self) -> float:
        """获取完成百分比"""
        if self.required == 0:
            return 100.0
        return (self.current / self.required) * 100.0


class QuestReward(BaseModel):
    """任务奖励"""

    exp: int = 0
    gold: int = 0
    items: List[Dict[str, Any]] = Field(default_factory=list)

    def add_item(self, item_id: str, quantity: int = 1):
        """添加物品奖励"""
        self.items.append({"id": item_id, "quantity": quantity})


class Quest(BaseModel):
    """任务

    完整的任务定义，包含类型、目标、奖励等
    """

    id: str
    type: QuestType
    title: str
    description: str
    level_requirement: int = 1

    # 目标和进度
    objectives: List[QuestObjective]
    status: QuestStatus = QuestStatus.AVAILABLE

    # 奖励
    rewards: QuestReward

    # 关联
    prerequisite_quests: List[str] = Field(default_factory=list)
    next_quests: List[str] = Field(default_factory=list)

    # 元数据
    giver_npc: Optional[str] = None
    location: Optional[str] = None

    def is_available(self, player_level: int, completed_quests: List[str]) -> bool:
        """检查任务是否可接取

        Args:
            player_level: 玩家等级
            completed_quests: 已完成的任务ID列表

        Returns:
            是否满足接取条件
        """
        # 检查等级要求
        if player_level < self.level_requirement:
            return False

        # 检查前置任务
        for prereq in self.prerequisite_quests:
            if prereq not in completed_quests:
                return False

        return True

    def activate(self) -> bool:
        """激活任务

        Returns:
            是否成功激活
        """
        if self.status == QuestStatus.AVAILABLE:
            self.status = QuestStatus.ACTIVE
            return True
        return False

    def complete(self) -> bool:
        """完成任务

        Returns:
            是否成功完成
        """
        # 检查所有目标是否完成
        if not all(obj.completed for obj in self.objectives):
            return False

        if self.status == QuestStatus.ACTIVE:
            self.status = QuestStatus.COMPLETED
            return True
        return False

    def fail(self):
        """标记任务为失败"""
        self.status = QuestStatus.FAILED

    def get_progress(self) -> Dict[str, Any]:
        """获取任务进度信息

        Returns:
            包含各目标进度的字典
        """
        completed_objectives = sum(1 for obj in self.objectives if obj.completed)
        total_objectives = len(self.objectives)

        return {
            "quest_id": self.id,
            "title": self.title,
            "status": self.status,
            "objectives_completed": completed_objectives,
            "objectives_total": total_objectives,
            "progress_percent": (
                (completed_objectives / total_objectives * 100) if total_objectives > 0 else 0
            ),
            "objectives": [
                {
                    "id": obj.id,
                    "description": obj.description,
                    "current": obj.current,
                    "required": obj.required,
                    "completed": obj.completed,
                    "progress_percent": obj.get_progress_percent(),
                }
                for obj in self.objectives
            ],
        }

    def update_objective(self, objective_id: str, amount: int = 1) -> bool:
        """更新指定目标的进度

        Args:
            objective_id: 目标ID
            amount: 进度增加量

        Returns:
            目标是否完成
        """
        for obj in self.objectives:
            if obj.id == objective_id:
                return obj.update_progress(amount)
        return False


# ==================== 辅助函数 ====================


def create_quest_from_dict(data: Dict[str, Any]) -> Quest:
    """从字典创建 Quest 对象

    Args:
        data: 包含任务数据的字典

    Returns:
        Quest 对象
    """
    # 转换 objectives
    objectives = []
    for obj_data in data.get("objectives", []):
        objectives.append(QuestObjective(**obj_data))

    # 转换 rewards
    rewards_data = data.get("rewards", {})
    rewards = QuestReward(**rewards_data)

    # 创建 Quest
    quest = Quest(
        id=data["id"],
        type=QuestType(data.get("type", "side")),
        title=data["title"],
        description=data["description"],
        level_requirement=data.get("level_requirement", 1),
        objectives=objectives,
        status=QuestStatus(data.get("status", "available")),
        rewards=rewards,
        prerequisite_quests=data.get("prerequisite_quests", []),
        next_quests=data.get("next_quests", []),
        giver_npc=data.get("giver_npc"),
        location=data.get("location"),
    )

    return quest
