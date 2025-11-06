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
    quest_id: Optional[str] = None  # 可选的任务ID（用于兼容）
    title: str
    description: str
    status: Literal["inactive", "active", "completed", "failed"] = "inactive"
    hints: List[str] = []
    objectives: List[QuestObjective] = []
    rewards: Dict[str, Any] = {}  # 任务奖励（exp, money, items等）


class WorldState(BaseModel):
    time: int = 0  # 回合数
    flags: Dict[str, Any] = {}
    discoveredLocations: List[str] = []
    variables: Dict[str, Any] = {}
    currentScene: Optional[str] = None
    theme: Optional[str] = None  # 世界主题/基调


class MapNode(BaseModel):
    id: str
    name: str
    shortDesc: str
    discovered: bool = False
    locked: bool = False
    keyRequired: Optional[str] = None
    metadata: Dict[str, Any] = {}  # 节点元数据（生态、坐标、POI等）


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
    turn_number: int = 0  # 当前回合数
    player: PlayerState
    world: WorldState
    quests: List[Quest] = []
    map: GameMap
    log: List[GameLogEntry] = []
    metadata: Dict[str, Any] = {}  # 元数据（创建时间、世界包ID等）


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

    def __init__(self, state: GameState, db_manager=None):
        """
        Args:
            state: 游戏状态
            db_manager: 数据库管理器（用于存档功能，可选）
        """
        self.state = state
        self.db_manager = db_manager

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

    # ---------- 任务系统增强 ----------

    def create_quest(
        self,
        quest_id: str,
        title: str,
        description: str,
        objectives: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """创建新任务"""
        # 检查任务是否已存在
        if any(q.id == quest_id for q in self.state.quests):
            return False

        # 构建目标列表
        quest_objectives = []
        if objectives:
            for obj in objectives:
                quest_objectives.append(QuestObjective(
                    id=obj.get("id", f"{quest_id}_obj_{len(quest_objectives)}"),
                    description=obj.get("description", ""),
                    completed=obj.get("completed", False),
                    required=obj.get("required", True)
                ))

        # 创建任务
        new_quest = Quest(
            id=quest_id,
            title=title,
            description=description,
            status="active",
            objectives=quest_objectives
        )
        self.state.quests.append(new_quest)
        return True

    def complete_quest(self, quest_id: str, rewards: Optional[Dict[str, Any]] = None) -> bool:
        """完成任务并发放奖励"""
        for quest in self.state.quests:
            if quest.id == quest_id:
                quest.status = "completed"

                # 发放奖励
                if rewards:
                    if "exp" in rewards:
                        self.add_exp(rewards["exp"])
                    if "gold" in rewards:
                        self.state.player.money += rewards.get("gold", 0)
                    if "items" in rewards:
                        for item in rewards["items"]:
                            self.add_item(
                                item_id=item.get("id"),
                                name=item.get("name"),
                                quantity=item.get("quantity", 1)
                            )
                return True
        return False

    # ---------- 经验值与升级系统 ----------

    def add_exp(self, amount: int) -> Dict[str, Any]:
        """增加经验值，自动检测升级"""
        # 确保玩家状态有经验值字段
        if not hasattr(self.state.player, "exp"):
            # 动态添加经验值字段
            self.state.player.__dict__["exp"] = 0
            self.state.player.__dict__["level"] = 1

        old_exp = self.state.player.__dict__.get("exp", 0)
        old_level = self.state.player.__dict__.get("level", 1)

        new_exp = old_exp + amount
        self.state.player.__dict__["exp"] = new_exp

        # 检查是否升级（简单的经验值公式：每级需要 100 * level 经验）
        exp_needed = self._calculate_exp_for_next_level(old_level)
        leveled_up = False
        new_level = old_level

        while new_exp >= exp_needed:
            new_exp -= exp_needed
            new_level += 1
            exp_needed = self._calculate_exp_for_next_level(new_level)
            leveled_up = True

        if leveled_up:
            self.level_up(new_level)

        return {
            "old_exp": old_exp,
            "new_exp": self.state.player.__dict__["exp"],
            "old_level": old_level,
            "new_level": self.state.player.__dict__["level"],
            "leveled_up": leveled_up
        }

    def _calculate_exp_for_next_level(self, current_level: int) -> int:
        """计算下一级所需经验值"""
        return 100 * current_level

    def level_up(self, new_level: int) -> Dict[str, Any]:
        """升级（提升属性）"""
        old_level = self.state.player.__dict__.get("level", 1)
        self.state.player.__dict__["level"] = new_level

        # 每级增加最大HP和体力
        hp_gain = 10
        stamina_gain = 5

        old_max_hp = self.state.player.maxHp
        old_max_stamina = self.state.player.maxStamina

        self.state.player.maxHp += hp_gain * (new_level - old_level)
        self.state.player.maxStamina += stamina_gain * (new_level - old_level)

        # 完全恢复HP和体力
        self.state.player.hp = self.state.player.maxHp
        self.state.player.stamina = self.state.player.maxStamina

        return {
            "old_level": old_level,
            "new_level": new_level,
            "hp_gain": hp_gain * (new_level - old_level),
            "stamina_gain": stamina_gain * (new_level - old_level),
            "new_max_hp": self.state.player.maxHp,
            "new_max_stamina": self.state.player.maxStamina
        }

    # ---------- 物品使用系统 ----------

    def use_item(self, item_id: str) -> Dict[str, Any]:
        """使用物品（仅消耗品）"""
        item = self.get_inventory_item(item_id)
        if not item:
            return {"success": False, "message": "物品不存在"}

        if item.type != "consumable":
            return {"success": False, "message": "该物品无法使用"}

        # 根据物品属性执行效果
        effects = item.properties.get("effects", {})
        result = {"success": True, "effects_applied": []}

        if "hp" in effects:
            hp_restored = effects["hp"]
            self.update_hp(hp_restored)
            result["effects_applied"].append(f"恢复 {hp_restored} HP")

        if "stamina" in effects:
            stamina_restored = effects["stamina"]
            self.update_stamina(stamina_restored)
            result["effects_applied"].append(f"恢复 {stamina_restored} 耐力")

        if "buff" in effects:
            buff = effects["buff"]
            # 这里可以实现buff系统（暂时跳过）
            result["effects_applied"].append(f"获得增益: {buff}")

        # 消耗物品
        self.remove_item(item_id, 1)
        result["message"] = f"使用了 {item.name}"

        return result

    # ---------- 战斗系统 ----------

    def roll_attack(
        self,
        weapon_bonus: int = 0,
        advantage: bool = False
    ) -> Dict[str, Any]:
        """攻击检定（1d20 + 武器加成）"""
        if advantage:
            roll = max(random.randint(1, 20), random.randint(1, 20))
        else:
            roll = random.randint(1, 20)

        total = roll + weapon_bonus
        critical_hit = roll == 20
        critical_miss = roll == 1

        return {
            "roll": roll,
            "bonus": weapon_bonus,
            "total": total,
            "critical_hit": critical_hit,
            "critical_miss": critical_miss,
            "damage_multiplier": 2 if critical_hit else 1
        }

    def calculate_damage(
        self,
        base_damage: int,
        attack_roll: Dict[str, Any],
        armor_class: int = 10
    ) -> Dict[str, Any]:
        """计算伤害"""
        hit = attack_roll["total"] >= armor_class

        if not hit:
            return {"hit": False, "damage": 0}

        damage = base_damage * attack_roll.get("damage_multiplier", 1)

        return {
            "hit": True,
            "damage": damage,
            "critical": attack_roll.get("critical_hit", False)
        }

    # ---------- 记忆查询 ----------

    def query_memory(self, query: str, limit: int = 5) -> List[GameLogEntry]:
        """查询游戏记忆（简单版：返回最近N条）"""
        # TODO: 实现向量检索或关键词匹配
        return self.state.log[-limit:]

    # ---------- 存档系统 ----------

    def save_game(
        self,
        slot_id: int,
        save_name: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """保存游戏到存档槽位"""
        if not self.db_manager:
            return {
                "success": False,
                "message": "存档功能未启用（需要数据库管理器）"
            }

        if not (1 <= slot_id <= 10):
            return {
                "success": False,
                "message": "存档槽位必须在 1-10 之间"
            }

        try:
            # 将GameState转换为字典
            game_state_dict = self.state.model_dump()

            # 保存到数据库
            save_id = self.db_manager.save_game(
                user_id=user_id,
                slot_id=slot_id,
                save_name=save_name,
                game_state=game_state_dict
            )

            return {
                "success": True,
                "save_id": save_id,
                "slot_id": slot_id,
                "save_name": save_name,
                "message": f"游戏已保存到槽位 {slot_id}"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"保存失败: {str(e)}"
            }

    def load_game(self, save_id: int) -> Dict[str, Any]:
        """加载存档"""
        if not self.db_manager:
            return {
                "success": False,
                "message": "存档功能未启用（需要数据库管理器）"
            }

        try:
            save_data = self.db_manager.load_game(save_id)
            if not save_data:
                return {
                    "success": False,
                    "message": f"存档 {save_id} 不存在"
                }

            # 加载游戏状态
            loaded_state = GameState(**save_data["game_state"])

            # 更新当前状态（注意：这会完全替换状态）
            self.state.__dict__.update(loaded_state.__dict__)

            return {
                "success": True,
                "save_id": save_id,
                "metadata": save_data["metadata"],
                "message": "存档加载成功"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"加载失败: {str(e)}"
            }

    def list_saves(self, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """列出所有存档"""
        if not self.db_manager:
            return []

        return self.db_manager.get_saves(user_id)

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
            },
            {
                "name": "create_quest",
                "description": "创建新任务",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "quest_id": {"type": "string", "description": "任务唯一ID"},
                        "title": {"type": "string", "description": "任务标题"},
                        "description": {"type": "string", "description": "任务描述"},
                        "objectives": {
                            "type": "array",
                            "description": "任务目标列表",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "description": {"type": "string"},
                                    "completed": {"type": "boolean"},
                                    "required": {"type": "boolean"}
                                }
                            }
                        }
                    },
                    "required": ["quest_id", "title", "description"]
                }
            },
            {
                "name": "complete_quest",
                "description": "完成任务并发放奖励",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "quest_id": {"type": "string"},
                        "rewards": {
                            "type": "object",
                            "description": "任务奖励",
                            "properties": {
                                "exp": {"type": "integer"},
                                "gold": {"type": "integer"},
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},
                                            "name": {"type": "string"},
                                            "quantity": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "required": ["quest_id"]
                }
            },
            {
                "name": "add_exp",
                "description": "增加经验值，自动检测升级",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "integer", "description": "经验值数量"}
                    },
                    "required": ["amount"]
                }
            },
            {
                "name": "use_item",
                "description": "使用消耗品（恢复HP、体力等）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string"}
                    },
                    "required": ["item_id"]
                }
            },
            {
                "name": "roll_attack",
                "description": "进行攻击检定（用于战斗）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "weapon_bonus": {"type": "integer", "default": 0},
                        "advantage": {"type": "boolean", "default": False}
                    },
                    "required": []
                }
            },
            {
                "name": "calculate_damage",
                "description": "根据攻击检定计算伤害",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "base_damage": {"type": "integer", "description": "基础伤害"},
                        "attack_roll": {"type": "object", "description": "攻击检定结果"},
                        "armor_class": {"type": "integer", "default": 10, "description": "目标护甲等级"}
                    },
                    "required": ["base_damage", "attack_roll"]
                }
            },
            {
                "name": "save_game",
                "description": "保存游戏到指定存档槽位（1-10）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "slot_id": {
                            "type": "integer",
                            "description": "存档槽位（1-10）",
                            "minimum": 1,
                            "maximum": 10
                        },
                        "save_name": {"type": "string", "description": "存档名称"}
                    },
                    "required": ["slot_id", "save_name"]
                }
            },
            {
                "name": "load_game",
                "description": "加载指定存档",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "save_id": {"type": "integer", "description": "存档ID"}
                    },
                    "required": ["save_id"]
                }
            },
            {
                "name": "list_saves",
                "description": "列出所有存档",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
