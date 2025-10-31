"""世界状态数据模型"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class Location:
    """地点状态"""
    id: str
    name: str
    type: str  # 城市/秘境/宗门等
    description: str
    properties: Dict[str, Any] = field(default_factory=dict)
    accessible_from: List[str] = field(default_factory=list)  # 可达地点列表


@dataclass
class Character:
    """角色状态"""
    id: str
    name: str
    role: str  # protagonist/ally/enemy/neutral
    description: str

    # 属性
    attributes: Dict[str, float] = field(default_factory=dict)

    # 资源
    resources: Dict[str, float] = field(default_factory=dict)

    # 装备/物品
    inventory: List[str] = field(default_factory=list)

    # 关系网络
    relationships: Dict[str, float] = field(default_factory=dict)  # {char_id: 好感度}

    # 当前状态
    location: str = ""
    status: str = "normal"  # normal/injured/exhausted等

    # 特殊能力
    abilities: List[str] = field(default_factory=list)


@dataclass
class Faction:
    """势力/组织"""
    id: str
    name: str
    type: str  # 宗门/财团/政府等
    alignment: str  # 正道/魔道/中立 或 敌对/友好/中立

    # 资源与实力
    resources: Dict[str, float] = field(default_factory=dict)
    power_level: float = 0.0

    # 成员
    members: List[str] = field(default_factory=list)  # character_ids
    leader: Optional[str] = None

    # 关系
    relationships: Dict[str, float] = field(default_factory=dict)  # {faction_id: 关系值}

    # 控制区域
    territories: List[str] = field(default_factory=list)  # location_ids


@dataclass
class Resource:
    """资源池"""
    type: str  # 灵石/信用点/灵材等
    amount: float
    max_capacity: Optional[float] = None
    regeneration_rate: float = 0.0  # 每回合恢复量


@dataclass
class WorldState:
    """世界状态（游戏状态快照）"""
    timestamp: int  # 游戏内时间戳
    turn: int = 0  # 回合数

    # 核心状态
    locations: Dict[str, Location] = field(default_factory=dict)
    characters: Dict[str, Character] = field(default_factory=dict)
    factions: Dict[str, Faction] = field(default_factory=dict)
    resources: Dict[str, Resource] = field(default_factory=dict)

    # 事件历史
    events_log: List[Dict[str, Any]] = field(default_factory=list)

    # 全局标志位
    flags: Dict[str, bool] = field(default_factory=dict)

    # 激活的效果/buff/debuff
    active_effects: List[Dict[str, Any]] = field(default_factory=list)

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get_protagonist(self) -> Optional[Character]:
        """获取主角"""
        for char in self.characters.values():
            if char.role == "protagonist":
                return char
        return None

    def add_event(self, event: Dict[str, Any]):
        """添加事件到历史记录"""
        self.events_log.append({
            "timestamp": self.timestamp,
            "turn": self.turn,
            **event
        })
        self.updated_at = datetime.now()

    def apply_state_patch(self, patch: Dict[str, Any]):
        """应用状态补丁"""
        # 更新角色
        if "characters" in patch:
            for char_id, updates in patch["characters"].items():
                if char_id in self.characters:
                    char = self.characters[char_id]
                    for key, value in updates.items():
                        if hasattr(char, key):
                            setattr(char, key, value)

        # 更新资源
        if "resources" in patch:
            for res_type, delta in patch["resources"].items():
                if res_type in self.resources:
                    self.resources[res_type].amount += delta
                else:
                    self.resources[res_type] = Resource(type=res_type, amount=delta)

        # 更新标志位
        if "flags" in patch:
            self.flags.update(patch["flags"])

        # 更新地点
        if "locations" in patch:
            for loc_id, updates in patch["locations"].items():
                if loc_id in self.locations:
                    loc = self.locations[loc_id]
                    for key, value in updates.items():
                        if hasattr(loc, key):
                            setattr(loc, key, value)

        # 更新势力
        if "factions" in patch:
            for faction_id, updates in patch["factions"].items():
                if faction_id in self.factions:
                    faction = self.factions[faction_id]
                    for key, value in updates.items():
                        if hasattr(faction, key):
                            setattr(faction, key, value)

        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        return {
            "timestamp": self.timestamp,
            "turn": self.turn,
            "locations": {k: v.__dict__ for k, v in self.locations.items()},
            "characters": {k: v.__dict__ for k, v in self.characters.items()},
            "factions": {k: v.__dict__ for k, v in self.factions.items()},
            "resources": {k: v.__dict__ for k, v in self.resources.items()},
            "events_log": self.events_log,
            "flags": self.flags,
            "active_effects": self.active_effects,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
