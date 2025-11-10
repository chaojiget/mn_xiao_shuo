"""NPC 系统数据模型

Phase 2 - NPC 系统实现
定义 NPC 相关的数据结构：NPC, NPCPersonality, NPCMemory
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NPCStatus(str, Enum):
    """NPC 状态"""

    SEED = "seed"  # 种子状态（仅概念，未实例化）
    ACTIVE = "active"  # 活跃（可交互）
    INACTIVE = "inactive"  # 非活跃（暂时不可见）
    RETIRED = "retired"  # 退役（剧情结束）


class NPCPersonality(BaseModel):
    """NPC 性格"""

    traits: List[str] = Field(default_factory=list)  # 性格特征列表
    values: Dict[str, int] = Field(default_factory=dict)  # 价值观（如：正义=8, 贪婪=3）
    speech_style: str = ""  # 说话风格描述

    def add_trait(self, trait: str):
        """添加性格特征"""
        if trait not in self.traits:
            self.traits.append(trait)

    def set_value(self, value_name: str, score: int):
        """设置价值观分数（0-10）"""
        self.values[value_name] = max(0, min(10, score))


class NPCMemory(BaseModel):
    """NPC 记忆"""

    turn_number: int
    event_type: str  # conversation/quest/combat/observation
    summary: str
    emotional_impact: int = 0  # -10 到 +10，负数为负面情绪，正数为正面情绪
    participants: List[str] = Field(default_factory=list)  # 参与者ID列表

    def is_recent(self, current_turn: int, window: int = 10) -> bool:
        """检查是否为最近记忆"""
        return current_turn - self.turn_number <= window


class NPCRelationship(BaseModel):
    """NPC 与其他角色的关系"""

    target_id: str  # 目标角色ID（玩家或其他NPC）
    affinity: int = 0  # 好感度 (-100 到 +100)
    trust: int = 0  # 信任度 (0 到 100)
    relationship_type: str = "stranger"  # stranger/acquaintance/friend/enemy/ally

    def adjust_affinity(self, delta: int):
        """调整好感度"""
        self.affinity = max(-100, min(100, self.affinity + delta))
        self._update_relationship_type()

    def adjust_trust(self, delta: int):
        """调整信任度"""
        self.trust = max(0, min(100, self.trust + delta))

    def _update_relationship_type(self):
        """根据好感度自动更新关系类型"""
        if self.affinity >= 75:
            self.relationship_type = "ally"
        elif self.affinity >= 50:
            self.relationship_type = "friend"
        elif self.affinity >= 0:
            self.relationship_type = "acquaintance"
        elif self.affinity >= -50:
            self.relationship_type = "stranger"
        else:
            self.relationship_type = "enemy"


class NPC(BaseModel):
    """NPC 完整数据模型"""

    id: str
    name: str
    role: str  # 职业/角色（如：商人、铁匠、守卫、村长）
    description: str = ""  # 外貌和背景描述
    status: NPCStatus = NPCStatus.SEED

    # 属性
    level: int = 1
    personality: NPCPersonality = Field(default_factory=NPCPersonality)

    # 记忆和目标
    memories: List[NPCMemory] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)

    # 关系
    relationships: List[NPCRelationship] = Field(default_factory=list)

    # 位置和任务
    current_location: Optional[str] = None
    available_quests: List[str] = Field(default_factory=list)

    # 对话相关
    dialogue_state: Dict[str, Any] = Field(default_factory=dict)  # 对话状态（如：已讨论的话题）

    def activate(self, location: str):
        """激活 NPC（从 seed 到 active）"""
        self.status = NPCStatus.ACTIVE
        self.current_location = location

    def retire(self):
        """退役 NPC"""
        self.status = NPCStatus.RETIRED

    def add_memory(
        self,
        turn_number: int,
        event_type: str,
        summary: str,
        emotional_impact: int = 0,
        participants: Optional[List[str]] = None,
    ):
        """添加记忆"""
        memory = NPCMemory(
            turn_number=turn_number,
            event_type=event_type,
            summary=summary,
            emotional_impact=emotional_impact,
            participants=participants or [],
        )
        self.memories.append(memory)

        # 保留最近的 50 条记忆
        if len(self.memories) > 50:
            self.memories = self.memories[-50:]

    def get_recent_memories(self, current_turn: int, count: int = 5) -> List[NPCMemory]:
        """获取最近的记忆"""
        recent = [m for m in self.memories if m.is_recent(current_turn, window=20)]
        return sorted(recent, key=lambda m: m.turn_number, reverse=True)[:count]

    def get_relationship(self, target_id: str) -> Optional[NPCRelationship]:
        """获取与某角色的关系"""
        return next((r for r in self.relationships if r.target_id == target_id), None)

    def update_relationship(self, target_id: str, affinity_delta: int = 0, trust_delta: int = 0):
        """更新关系"""
        relationship = self.get_relationship(target_id)
        if not relationship:
            relationship = NPCRelationship(target_id=target_id)
            self.relationships.append(relationship)

        if affinity_delta != 0:
            relationship.adjust_affinity(affinity_delta)
        if trust_delta != 0:
            relationship.adjust_trust(trust_delta)

    def add_quest(self, quest_id: str):
        """添加可提供的任务"""
        if quest_id not in self.available_quests:
            self.available_quests.append(quest_id)

    def remove_quest(self, quest_id: str):
        """移除任务（已接取或过期）"""
        if quest_id in self.available_quests:
            self.available_quests.remove(quest_id)

    def get_dialogue_context(self, current_turn: int) -> str:
        """获取对话上下文（用于生成对话）"""
        context_parts = []

        # 基本信息
        context_parts.append(f"你是{self.name}，一个{self.role}。")

        # 性格
        if self.personality.traits:
            context_parts.append(f"性格特征: {', '.join(self.personality.traits)}")
        if self.personality.speech_style:
            context_parts.append(f"说话风格: {self.personality.speech_style}")

        # 目标
        if self.goals:
            context_parts.append("当前目标:")
            for goal in self.goals:
                context_parts.append(f"- {goal}")

        # 最近记忆
        recent_memories = self.get_recent_memories(current_turn, count=3)
        if recent_memories:
            context_parts.append("\n最近记忆:")
            for mem in recent_memories:
                context_parts.append(f"- 回合{mem.turn_number}: {mem.summary}")
        else:
            context_parts.append("\n（首次见面）")

        return "\n".join(context_parts)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于存储）"""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "status": self.status.value,
            "level": self.level,
            "personality": self.personality.model_dump(),
            "memories": [m.model_dump() for m in self.memories],
            "goals": self.goals,
            "relationships": [r.model_dump() for r in self.relationships],
            "current_location": self.current_location,
            "available_quests": self.available_quests,
            "dialogue_state": self.dialogue_state,
        }


# ==================== 辅助函数 ====================


def create_npc_from_dict(data: Dict[str, Any]) -> NPC:
    """从字典创建 NPC 对象

    Args:
        data: 包含 NPC 数据的字典

    Returns:
        NPC 对象
    """
    # 转换 personality
    personality_data = data.get("personality", {})
    personality = NPCPersonality(**personality_data)

    # 转换 memories
    memories = []
    for mem_data in data.get("memories", []):
        memories.append(NPCMemory(**mem_data))

    # 转换 relationships
    relationships = []
    for rel_data in data.get("relationships", []):
        relationships.append(NPCRelationship(**rel_data))

    # 创建 NPC
    npc = NPC(
        id=data["id"],
        name=data["name"],
        role=data["role"],
        description=data.get("description", ""),
        status=NPCStatus(data.get("status", "seed")),
        level=data.get("level", 1),
        personality=personality,
        memories=memories,
        goals=data.get("goals", []),
        relationships=relationships,
        current_location=data.get("current_location"),
        available_quests=data.get("available_quests", []),
        dialogue_state=data.get("dialogue_state", {}),
    )

    return npc
