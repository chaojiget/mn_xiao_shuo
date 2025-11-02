"""
游戏工具系统 - Agent可调用的工具函数
提供状态读写、检定、记忆查询等功能
"""

import random
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field


# ==================== 数据模型 ====================

class InventoryItem(BaseModel):
    id: str
    name: str
    description: str
    quantity: int = 1
    type: Literal["weapon", "armor", "consumable", "key", "quest", "misc"] = "misc"
    properties: Dict[str, Any] = {}


class PlayerState(BaseModel):
    hp: int = 100
    maxHp: int = 100
    stamina: int = 100
    maxStamina: int = 100
    traits: List[str] = []
    inventory: List[InventoryItem] = []
    location: str = "start"
    money: int = 0


class QuestObjective(BaseModel):
    id: str
    description: str
    completed: bool = False
    required: bool = True


class Quest(BaseModel):
    id: str
    title: str
    description: str
    status: Literal["inactive", "active", "completed", "failed"] = "inactive"
    hints: List[str] = []
    objectives: List[QuestObjective] = []


class WorldState(BaseModel):
    time: int = 0  # 回合数
    flags: Dict[str, Any] = {}
    discoveredLocations: List[str] = []
    variables: Dict[str, Any] = {}
    currentScene: Optional[str] = None


class MapNode(BaseModel):
    id: str
    name: str
    shortDesc: str
    discovered: bool = False
    locked: bool = False
    keyRequired: Optional[str] = None


class MapEdge(BaseModel):
    fromNode: str = Field(alias="from")
    toNode: str = Field(alias="to")
    bidirectional: bool = True

    class Config:
        populate_by_name = True  # 允许使用原始字段名或别名


class GameMap(BaseModel):
    nodes: List[MapNode] = []
    edges: List[MapEdge] = []
    currentNodeId: str = "start"


class GameLogEntry(BaseModel):
    turn: int
    actor: Literal["player", "system", "npc"]
    text: str
    timestamp: int


class GameState(BaseModel):
    version: str = "1.0.0"
    player: PlayerState
    world: WorldState
    quests: List[Quest] = []
    map: GameMap
    log: List[GameLogEntry] = []


# ==================== 检定系统 ====================

class RollCheckParams(BaseModel):
    type: Literal[
        "survival", "stealth", "persuasion", "perception",
        "strength", "intelligence", "luck", "custom"
    ]
    dc: int  # Difficulty Class
    modifier: int = 0
    advantage: bool = False
    disadvantage: bool = False


class RollCheckResult(BaseModel):
    success: bool
    roll: int
    total: int
    dc: int
    margin: int
    critical: bool = False


def roll_check(params: RollCheckParams) -> RollCheckResult:
    """执行检定骰点"""
    # 掷骰（1d20）
    if params.advantage:
        roll = max(random.randint(1, 20), random.randint(1, 20))
    elif params.disadvantage:
        roll = min(random.randint(1, 20), random.randint(1, 20))
    else:
        roll = random.randint(1, 20)

    total = roll + params.modifier
    success = total >= params.dc
    margin = total - params.dc

    # 大成功/大失败判定
    critical = roll == 20 or roll == 1

    return RollCheckResult(
        success=success,
        roll=roll,
        total=total,
        dc=params.dc,
        margin=margin,
        critical=critical
    )


# ==================== 游戏工具类 ====================

class GameTools:
    """游戏工具集 - 提供给Agent的函数接口"""

    def __init__(self, state: GameState):
        self.state = state

    # ---------- 状态读取 ----------

    def get_state(self) -> GameState:
        """获取完整游戏状态"""
        return self.state

    def get_player_state(self) -> PlayerState:
        """获取玩家状态"""
        return self.state.player

    def get_world_state(self) -> WorldState:
        """获取世界状态"""
        return self.state.world

    def get_quests(self, status: Optional[str] = None) -> List[Quest]:
        """获取任务列表"""
        if status:
            return [q for q in self.state.quests if q.status == status]
        return self.state.quests

    def get_location(self, location_id: Optional[str] = None) -> Optional[MapNode]:
        """获取地点信息"""
        if location_id is None:
            location_id = self.state.player.location

        for node in self.state.map.nodes:
            if node.id == location_id:
                return node
        return None

    def get_inventory_item(self, item_id: str) -> Optional[InventoryItem]:
        """获取背包物品"""
        for item in self.state.player.inventory:
            if item.id == item_id:
                return item
        return None

    # ---------- 状态修改 ----------

    def add_item(self, item_id: str, name: str, quantity: int = 1, **kwargs) -> bool:
        """添加物品到背包"""
        existing = self.get_inventory_item(item_id)
        if existing:
            existing.quantity += quantity
            return True

        new_item = InventoryItem(
            id=item_id,
            name=name,
            quantity=quantity,
            description=kwargs.get("description", ""),
            type=kwargs.get("type", "misc"),
            properties=kwargs.get("properties", {})
        )
        self.state.player.inventory.append(new_item)
        return True

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """移除背包物品"""
        item = self.get_inventory_item(item_id)
        if not item:
            return False

        if item.quantity <= quantity:
            self.state.player.inventory.remove(item)
        else:
            item.quantity -= quantity
        return True

    def update_hp(self, delta: int) -> int:
        """更新生命值"""
        self.state.player.hp = max(0, min(self.state.player.maxHp, self.state.player.hp + delta))
        return self.state.player.hp

    def update_stamina(self, delta: int) -> int:
        """更新体力值"""
        self.state.player.stamina = max(0, min(
            self.state.player.maxStamina,
            self.state.player.stamina + delta
        ))
        return self.state.player.stamina

    def set_location(self, location_id: str) -> bool:
        """设置玩家位置"""
        node = self.get_location(location_id)
        if not node:
            return False

        self.state.player.location = location_id
        self.state.map.currentNodeId = location_id

        # 自动标记为已发现
        if location_id not in self.state.world.discoveredLocations:
            self.state.world.discoveredLocations.append(location_id)
            node.discovered = True

        return True

    def set_flag(self, key: str, value: Any) -> None:
        """设置全局标志位"""
        self.state.world.flags[key] = value

    def get_flag(self, key: str, default: Any = None) -> Any:
        """获取全局标志位"""
        return self.state.world.flags.get(key, default)

    def update_quest(self, quest_id: str, **updates) -> bool:
        """更新任务状态"""
        for quest in self.state.quests:
            if quest.id == quest_id:
                for key, value in updates.items():
                    if hasattr(quest, key):
                        setattr(quest, key, value)
                return True
        return False

    def discover_location(self, location_id: str) -> bool:
        """发现新地点"""
        node = self.get_location(location_id)
        if not node:
            return False

        if location_id not in self.state.world.discoveredLocations:
            self.state.world.discoveredLocations.append(location_id)
            node.discovered = True
            return True
        return False

    def unlock_location(self, location_id: str) -> bool:
        """解锁地点"""
        node = self.get_location(location_id)
        if not node:
            return False

        node.locked = False
        return True

    def add_trait(self, trait: str) -> bool:
        """添加特质"""
        if trait not in self.state.player.traits:
            self.state.player.traits.append(trait)
            return True
        return False

    def remove_trait(self, trait: str) -> bool:
        """移除特质"""
        if trait in self.state.player.traits:
            self.state.player.traits.remove(trait)
            return True
        return False

    # ---------- 检定与随机 ----------

    def roll_check(
        self,
        type: str,
        dc: int,
        modifier: int = 0,
        advantage: bool = False,
        disadvantage: bool = False
    ) -> Dict[str, Any]:
        """执行检定"""
        # 创建params对象
        params = RollCheckParams(
            type=type,  # type: ignore
            dc=dc,
            modifier=modifier,
            advantage=advantage,
            disadvantage=disadvantage
        )

        # 根据特质添加修正值
        trait_bonuses = {
            "survival": ["野外生存", "追踪专家"],
            "stealth": ["潜行大师", "暗影行者"],
            "persuasion": ["魅力非凡", "口才出众"],
            "perception": ["敏锐感知", "鹰眼"],
            "strength": ["强壮", "力大无穷"],
            "intelligence": ["博学", "天才"],
        }

        if params.type in trait_bonuses:
            for trait in self.state.player.traits:
                if trait in trait_bonuses[params.type]:
                    params.modifier += 2  # 每个相关特质+2

        result = roll_check(params)
        return result.model_dump()

    # ---------- 记忆查询 ----------

    def query_memory(self, query: str, limit: int = 5) -> List[GameLogEntry]:
        """查询游戏记忆（简单版：返回最近N条）"""
        # TODO: 实现向量检索或关键词匹配
        return self.state.log[-limit:]

    # ---------- 日志记录 ----------

    def add_log(self, actor: str, text: str) -> None:
        """添加游戏日志"""
        import time
        entry = GameLogEntry(
            turn=self.state.world.time,
            actor=actor,  # type: ignore
            text=text,
            timestamp=int(time.time())
        )
        self.state.log.append(entry)

    # ---------- 工具描述（供LLM调用） ----------

    @staticmethod
    def get_tool_definitions() -> List[Dict[str, Any]]:
        """获取工具定义（Claude Tool格式）"""
        return [
            {
                "name": "get_state",
                "description": "获取当前完整游戏状态，包括玩家、世界、任务等",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_player_state",
                "description": "获取玩家当前状态（生命、体力、背包、位置等）",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "add_item",
                "description": "向玩家背包添加物品",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string", "description": "物品唯一ID"},
                        "name": {"type": "string", "description": "物品名称"},
                        "quantity": {"type": "integer", "description": "数量", "default": 1},
                        "description": {"type": "string", "description": "物品描述"},
                        "type": {"type": "string", "enum": ["weapon", "armor", "consumable", "key", "quest", "misc"]}
                    },
                    "required": ["item_id", "name"]
                }
            },
            {
                "name": "remove_item",
                "description": "从背包移除物品",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string"},
                        "quantity": {"type": "integer", "default": 1}
                    },
                    "required": ["item_id"]
                }
            },
            {
                "name": "update_hp",
                "description": "更新玩家生命值（正数增加，负数减少）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "delta": {"type": "integer", "description": "变化量"}
                    },
                    "required": ["delta"]
                }
            },
            {
                "name": "set_location",
                "description": "设置玩家当前位置",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location_id": {"type": "string"}
                    },
                    "required": ["location_id"]
                }
            },
            {
                "name": "set_flag",
                "description": "设置全局标志位（用于记录事件状态）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string"},
                        "value": {"description": "任意值（布尔、数字、字符串）"}
                    },
                    "required": ["key", "value"]
                }
            },
            {
                "name": "roll_check",
                "description": "执行技能检定（1d20+修正 vs 难度）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["survival", "stealth", "persuasion", "perception", "strength", "intelligence", "luck", "custom"]},
                        "dc": {"type": "integer", "description": "难度等级（Difficulty Class）"},
                        "modifier": {"type": "integer", "default": 0},
                        "advantage": {"type": "boolean", "default": False},
                        "disadvantage": {"type": "boolean", "default": False}
                    },
                    "required": ["type", "dc"]
                }
            },
            {
                "name": "update_quest",
                "description": "更新任务状态",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "quest_id": {"type": "string"},
                        "status": {"type": "string", "enum": ["inactive", "active", "completed", "failed"]},
                        "hints": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["quest_id"]
                }
            }
        ]
