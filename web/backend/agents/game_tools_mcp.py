"""
游戏工具系统 - 使用 Claude Agent SDK 的 @tool 装饰器
基于 docs/TECHNICAL_IMPLEMENTATION_PLAN.md 第4节设计
"""

from typing import Dict, Any
from claude_agent_sdk import tool
import random


# ============= 游戏状态管理 =============

# 全局游戏状态（实际应从数据库或session获取）
_game_states: Dict[str, Dict[str, Any]] = {}


class GameStateManager:
    """游戏状态管理器 - 处理数据库访问"""

    def __init__(self, db_connection):
        self.db = db_connection

    def get_state(self, session_id: str) -> Dict[str, Any]:
        """从数据库获取游戏状态"""
        # 先查内存缓存
        if session_id in _game_states:
            return _game_states[session_id]

        # 从数据库加载
        state = self.db.load_game_state(session_id) if self.db else None
        if state:
            _game_states[session_id] = state
            return state

        # 创建新状态
        return self._create_new_state(session_id)

    def save_state(self, session_id: str, state: Dict[str, Any]):
        """保存游戏状态到数据库"""
        _game_states[session_id] = state
        if self.db:
            self.db.save_game_state(session_id, state)

    def _create_new_state(self, session_id: str) -> Dict[str, Any]:
        """创建新游戏状态"""
        state = {
            "player": {
                "hp": 100,
                "max_hp": 100,
                "stamina": 100,
                "inventory": [],
                "gold": 0
            },
            "world": {
                "current_location": "起始村庄",
                "theme": "奇幻世界"
            },
            "turn_number": 0,
            "logs": []
        }
        _game_states[session_id] = state
        return state


# 全局状态管理器实例（在应用启动时初始化）
state_manager: GameStateManager = None


def init_state_manager(db_connection):
    """初始化状态管理器"""
    global state_manager
    state_manager = GameStateManager(db_connection)


# ============= MCP 工具定义 =============

# 当前会话ID（从上下文传入）
current_session_id: str = "default"


def set_session(session_id: str):
    """设置当前会话ID"""
    global current_session_id
    current_session_id = session_id


# ============= 工具装饰器定义 =============

@tool(
    "get_player_state",
    "获取玩家当前状态（HP、背包、位置等）",
    {
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def get_player_state(args: Dict) -> Dict[str, Any]:
    """获取玩家状态

    这个工具会从数据库读取游戏状态
    """
    state = state_manager.get_state(current_session_id)
    player = state.get('player', {})

    return {
        "hp": player.get('hp', 100),
        "max_hp": player.get('max_hp', 100),
        "stamina": player.get('stamina', 100),
        "location": state.get('world', {}).get('current_location'),
        "inventory": player.get('inventory', []),
        "gold": player.get('gold', 0)
    }


@tool(
    "add_item",
    "向玩家背包添加物品",
    {
        "type": "object",
        "properties": {
            "item_id": {
                "type": "string",
                "description": "物品ID"
            },
            "quantity": {
                "type": "integer",
                "description": "数量",
                "minimum": 1,
                "default": 1
            }
        },
        "required": ["item_id"]
    }
)
async def add_item(args: Dict) -> Dict[str, Any]:
    """添加物品到背包

    这个工具会修改游戏状态并保存到数据库
    """
    item_id = args['item_id']
    quantity = args.get('quantity', 1)

    # 从数据库获取状态
    state = state_manager.get_state(current_session_id)
    player = state.setdefault('player', {})
    inventory = player.setdefault('inventory', [])

    # 查找已存在的物品
    existing = next((item for item in inventory if item['id'] == item_id), None)

    if existing:
        existing['quantity'] += quantity
    else:
        inventory.append({
            "id": item_id,
            "name": item_id,
            "quantity": quantity
        })

    # 保存到数据库
    state_manager.save_state(current_session_id, state)

    return {
        "success": True,
        "message": f"获得了 {quantity} 个 {item_id}",
        "current_inventory": inventory
    }


@tool(
    "update_hp",
    "更新玩家HP",
    {
        "type": "object",
        "properties": {
            "change": {
                "type": "integer",
                "description": "HP变化量（正数为恢复，负数为伤害）"
            },
            "reason": {
                "type": "string",
                "description": "原因描述",
                "default": ""
            }
        },
        "required": ["change"]
    }
)
async def update_hp(args: Dict) -> Dict[str, Any]:
    """更新HP

    这个工具会修改HP并保存到数据库
    """
    change = args['change']
    reason = args.get('reason', '')

    state = state_manager.get_state(current_session_id)
    player = state.setdefault('player', {})

    old_hp = player.get('hp', 100)
    max_hp = player.get('max_hp', 100)

    new_hp = max(0, min(max_hp, old_hp + change))
    player['hp'] = new_hp

    # 记录日志
    logs = state.setdefault('logs', [])
    logs.append(f"HP变化: {old_hp} → {new_hp} ({reason})")

    # 保存到数据库
    state_manager.save_state(current_session_id, state)

    result = {
        "old_hp": old_hp,
        "new_hp": new_hp,
        "change": change,
        "reason": reason
    }

    if new_hp == 0:
        result["status"] = "死亡"
    elif new_hp < max_hp * 0.3:
        result["status"] = "危险"
    else:
        result["status"] = "正常"

    return result


@tool(
    "roll_check",
    "进行技能检定（d20系统）",
    {
        "type": "object",
        "properties": {
            "skill": {
                "type": "string",
                "description": "技能名称（如：力量、敏捷、感知）"
            },
            "dc": {
                "type": "integer",
                "description": "难度等级（DC）"
            },
            "modifier": {
                "type": "integer",
                "description": "修正值",
                "default": 0
            },
            "advantage": {
                "type": "boolean",
                "description": "是否有优势",
                "default": False
            }
        },
        "required": ["skill", "dc"]
    }
)
async def roll_check(args: Dict) -> Dict[str, Any]:
    """技能检定

    这个工具不需要访问数据库，只是执行随机检定
    """
    skill = args['skill']
    dc = args['dc']
    modifier = args.get('modifier', 0)
    advantage = args.get('advantage', False)

    if advantage:
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        roll = max(roll1, roll2)
        detail = f"优势检定: {roll1}, {roll2} -> {roll}"
    else:
        roll = random.randint(1, 20)
        detail = f"检定: {roll}"

    total = roll + modifier
    success = total >= dc

    # 记录到游戏日志
    state = state_manager.get_state(current_session_id)
    logs = state.setdefault('logs', [])
    logs.append(f"{skill}检定: {total} vs DC{dc} ({'成功' if success else '失败'})")
    state_manager.save_state(current_session_id, state)

    return {
        "skill": skill,
        "roll": roll,
        "modifier": modifier,
        "total": total,
        "dc": dc,
        "success": success,
        "detail": detail,
        "result": "成功!" if success else "失败!"
    }


@tool(
    "set_location",
    "设置玩家位置",
    {
        "type": "object",
        "properties": {
            "location_id": {
                "type": "string",
                "description": "位置ID"
            },
            "description": {
                "type": "string",
                "description": "位置描述",
                "default": ""
            }
        },
        "required": ["location_id"]
    }
)
async def set_location(args: Dict) -> Dict[str, Any]:
    """设置位置

    这个工具会更新世界状态并保存到数据库
    """
    location_id = args['location_id']
    description = args.get('description', '')

    state = state_manager.get_state(current_session_id)
    world = state.setdefault('world', {})

    old_location = world.get('current_location', '未知')
    world['current_location'] = location_id

    # 记录到日志
    logs = state.setdefault('logs', [])
    logs.append(f"从 {old_location} 移动到 {location_id}")

    # 保存到数据库
    state_manager.save_state(current_session_id, state)

    return {
        "success": True,
        "old_location": old_location,
        "new_location": location_id,
        "description": description
    }


@tool(
    "create_quest",
    "创建新任务并保存到数据库",
    {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "任务标题"},
            "description": {"type": "string", "description": "任务描述"},
            "objectives": {
                "type": "array",
                "description": "任务目标列表",
                "items": {"type": "object"}
            },
            "rewards": {
                "type": "object",
                "description": "任务奖励"
            }
        },
        "required": ["title", "description", "objectives", "rewards"]
    }
)
async def create_quest(args: Dict) -> Dict[str, Any]:
    """创建任务

    这个工具直接操作数据库
    """
    # 使用传入的quest_id或生成新的
    quest_id = args.get("quest_id")
    if not quest_id:
        quest_id = f"quest_{random.randint(1000, 9999)}"

    quest_data = {
        "id": quest_id,
        "type": args.get("quest_type", "main"),
        "title": args["title"],
        "description": args["description"],
        "level_requirement": args.get("level_requirement", 1),
        "objectives": args["objectives"],
        "rewards": args["rewards"],
        "status": "available"
    }

    # 保存到数据库
    if state_manager.db:
        state_manager.db.save_quest(quest_data)

    # 添加到游戏状态的quests数组
    state = state_manager.get_state(current_session_id)
    quests = state.setdefault('quests', [])
    quests.append(quest_data)
    state_manager.save_state(current_session_id, state)

    return {
        "success": True,
        "quest_id": quest_id,
        "message": f"任务 '{args['title']}' 创建成功"
    }


@tool(
    "get_quests",
    "获取任务列表（可筛选状态）",
    {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "任务状态筛选：available/active/completed/failed，不传则返回所有",
                "enum": ["available", "active", "completed", "failed"]
            }
        },
        "required": []
    }
)
async def get_quests(args: Dict) -> Dict[str, Any]:
    """获取任务列表"""
    state = state_manager.get_state(current_session_id)
    all_quests = state.get('quests', [])

    # 筛选状态
    status_filter = args.get('status')
    if status_filter:
        filtered_quests = [q for q in all_quests if q.get('status') == status_filter]
    else:
        filtered_quests = all_quests

    return {
        "quests": filtered_quests,
        "count": len(filtered_quests),
        "total": len(filtered_quests)
    }


@tool(
    "activate_quest",
    "激活任务（从available变为active）",
    {
        "type": "object",
        "properties": {
            "quest_id": {"type": "string", "description": "任务ID"}
        },
        "required": ["quest_id"]
    }
)
async def activate_quest(args: Dict) -> Dict[str, Any]:
    """激活任务"""
    quest_id = args['quest_id']

    state = state_manager.get_state(current_session_id)
    quests = state.get('quests', [])

    # 查找任务
    quest = next((q for q in quests if q.get('id') == quest_id), None)

    if not quest:
        return {
            "success": False,
            "message": f"任务 {quest_id} 不存在"
        }

    if quest.get('status') != 'available':
        return {
            "success": False,
            "message": f"任务状态为 {quest.get('status')}，无法激活"
        }

    # 激活任务
    quest['status'] = 'active'

    # 保存状态
    state_manager.save_state(current_session_id, state)

    return {
        "success": True,
        "quest_id": quest_id,
        "message": f"任务 '{quest.get('title')}' 已激活"
    }


@tool(
    "update_quest_objective",
    "更新任务目标进度",
    {
        "type": "object",
        "properties": {
            "quest_id": {"type": "string", "description": "任务ID"},
            "objective_id": {"type": "string", "description": "目标ID"},
            "amount": {"type": "integer", "description": "进度增加量", "default": 1}
        },
        "required": ["quest_id", "objective_id"]
    }
)
async def update_quest_objective(args: Dict) -> Dict[str, Any]:
    """更新任务目标进度"""
    quest_id = args['quest_id']
    objective_id = args['objective_id']
    amount = args.get('amount', 1)

    state = state_manager.get_state(current_session_id)
    quests = state.get('quests', [])

    # 查找任务
    quest = next((q for q in quests if q.get('id') == quest_id), None)

    if not quest:
        return {
            "success": False,
            "message": f"任务 {quest_id} 不存在"
        }

    # 查找目标
    objectives = quest.get('objectives', [])
    objective = next((obj for obj in objectives if obj.get('id') == objective_id), None)

    if not objective:
        return {
            "success": False,
            "message": f"目标 {objective_id} 不存在"
        }

    # 更新进度
    current = objective.get('current', 0)
    required = objective.get('required', 1)
    new_current = min(current + amount, required)
    objective['current'] = new_current
    objective['completed'] = new_current >= required

    # 保存状态
    state_manager.save_state(current_session_id, state)

    return {
        "success": True,
        "quest_id": quest_id,
        "objective_id": objective_id,
        "objective": {
            "id": objective_id,
            "description": objective.get('description', ''),
            "current": new_current,
            "required": required,
            "completed": objective['completed']
        },
        "current": new_current,
        "required": required,
        "completed": objective['completed'],
        "message": f"目标进度: {new_current}/{required}"
    }


@tool(
    "complete_quest",
    "完成任务并发放奖励",
    {
        "type": "object",
        "properties": {
            "quest_id": {"type": "string", "description": "任务ID"}
        },
        "required": ["quest_id"]
    }
)
async def complete_quest(args: Dict) -> Dict[str, Any]:
    """完成任务"""
    quest_id = args['quest_id']

    state = state_manager.get_state(current_session_id)
    quests = state.get('quests', [])

    # 查找任务
    quest = next((q for q in quests if q.get('id') == quest_id), None)

    if not quest:
        return {
            "success": False,
            "message": f"任务 {quest_id} 不存在"
        }

    # 检查所有目标是否完成
    objectives = quest.get('objectives', [])
    if not all(obj.get('completed', False) for obj in objectives):
        incomplete = [obj.get('description') for obj in objectives if not obj.get('completed', False)]
        return {
            "success": False,
            "message": f"任务未完成，剩余目标: {', '.join(incomplete)}"
        }

    # 发放奖励
    rewards = quest.get('rewards', {})
    player = state.setdefault('player', {})

    # 经验值
    exp_reward = rewards.get('exp', 0)
    if exp_reward > 0:
        current_exp = player.get('exp', 0)
        player['exp'] = current_exp + exp_reward

    # 金币
    gold_reward = rewards.get('gold', 0)
    if gold_reward > 0:
        current_gold = player.get('gold', 0)
        player['gold'] = current_gold + gold_reward

    # 物品
    item_rewards = rewards.get('items', [])
    inventory = player.setdefault('inventory', [])
    for item in item_rewards:
        item_id = item.get('id')
        quantity = item.get('quantity', 1)
        existing = next((inv_item for inv_item in inventory if inv_item['id'] == item_id), None)
        if existing:
            existing['quantity'] += quantity
        else:
            inventory.append({
                "id": item_id,
                "name": item.get('name', item_id),
                "quantity": quantity
            })

    # 标记任务为完成
    quest['status'] = 'completed'

    # 保存状态
    state_manager.save_state(current_session_id, state)

    return {
        "success": True,
        "quest_id": quest_id,
        "quest_title": quest.get('title'),
        "rewards": {
            "exp": exp_reward,
            "gold": gold_reward,
            "items": item_rewards
        },
        "message": f"任务 '{quest.get('title')}' 已完成！"
    }


@tool(
    "create_npc",
    "创建新的 NPC",
    {
        "type": "object",
        "properties": {
            "npc_id": {"type": "string", "description": "NPC唯一ID"},
            "name": {"type": "string", "description": "NPC名字"},
            "role": {"type": "string", "description": "职业/角色"},
            "description": {"type": "string", "description": "外貌和背景描述"},
            "location": {"type": "string", "description": "当前位置"},
            "personality_traits": {
                "type": "array",
                "description": "性格特征列表",
                "items": {"type": "string"},
                "default": []
            },
            "speech_style": {"type": "string", "description": "说话风格", "default": ""},
            "goals": {
                "type": "array",
                "description": "目标列表",
                "items": {"type": "string"},
                "default": []
            }
        },
        "required": ["npc_id", "name", "role", "location"]
    }
)
async def create_npc(args: Dict) -> Dict[str, Any]:
    """创建 NPC"""
    npc_data = {
        "id": args["npc_id"],
        "name": args["name"],
        "role": args["role"],
        "description": args.get("description", ""),
        "status": "active",
        "current_location": args["location"],
        "personality": {
            "traits": args.get("personality_traits", []),
            "speech_style": args.get("speech_style", "")
        },
        "goals": args.get("goals", []),
        "memories": [],
        "relationships": [],
        "available_quests": []
    }

    # 保存到游戏状态
    state = state_manager.get_state(current_session_id)
    npcs = state.setdefault('npcs', [])
    npcs.append(npc_data)
    state_manager.save_state(current_session_id, state)

    return {
        "success": True,
        "npc_id": args["npc_id"],
        "name": args["name"],
        "message": f"NPC '{args['name']}' 创建成功，位于 {args['location']}"
    }


@tool(
    "get_npcs",
    "获取 NPC 列表（可按位置筛选）",
    {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "位置筛选，不传则返回所有NPC"
            },
            "status": {
                "type": "string",
                "description": "状态筛选：active/inactive/retired",
                "enum": ["active", "inactive", "retired"]
            }
        },
        "required": []
    }
)
async def get_npcs(args: Dict) -> Dict[str, Any]:
    """获取 NPC 列表"""
    state = state_manager.get_state(current_session_id)
    all_npcs = state.get('npcs', [])

    # 筛选位置
    location_filter = args.get('location')
    if location_filter:
        filtered_npcs = [n for n in all_npcs if n.get('current_location') == location_filter]
    else:
        filtered_npcs = all_npcs

    # 筛选状态
    status_filter = args.get('status')
    if status_filter:
        filtered_npcs = [n for n in filtered_npcs if n.get('status') == status_filter]

    return {
        "npcs": filtered_npcs,
        "count": len(filtered_npcs),
        "total": len(filtered_npcs),
        "location": location_filter
    }


@tool(
    "update_npc_relationship",
    "更新 NPC 与玩家的关系",
    {
        "type": "object",
        "properties": {
            "npc_id": {"type": "string", "description": "NPC ID"},
            "affinity_delta": {
                "type": "integer",
                "description": "好感度变化（-100到+100）",
                "default": 0
            },
            "trust_delta": {
                "type": "integer",
                "description": "信任度变化（0到100）",
                "default": 0
            },
            "reason": {"type": "string", "description": "原因描述", "default": ""}
        },
        "required": ["npc_id"]
    }
)
async def update_npc_relationship(args: Dict) -> Dict[str, Any]:
    """更新 NPC 关系"""
    npc_id = args['npc_id']
    affinity_delta = args.get('affinity_delta', 0)
    trust_delta = args.get('trust_delta', 0)
    reason = args.get('reason', '')

    state = state_manager.get_state(current_session_id)
    npcs = state.get('npcs', [])

    # 查找 NPC
    npc = next((n for n in npcs if n.get('id') == npc_id), None)

    if not npc:
        return {
            "success": False,
            "message": f"NPC {npc_id} 不存在"
        }

    # 获取或创建与玩家的关系
    relationships = npc.setdefault('relationships', [])
    player_rel = next((r for r in relationships if r.get('target_id') == 'player'), None)

    if not player_rel:
        player_rel = {
            "target_id": "player",
            "affinity": 0,
            "trust": 0,
            "relationship_type": "stranger"
        }
        relationships.append(player_rel)

    # 更新关系
    old_affinity = player_rel['affinity']
    old_trust = player_rel['trust']

    player_rel['affinity'] = max(-100, min(100, old_affinity + affinity_delta))
    player_rel['trust'] = max(0, min(100, old_trust + trust_delta))

    # 更新关系类型
    affinity = player_rel['affinity']
    if affinity >= 75:
        player_rel['relationship_type'] = "ally"
    elif affinity >= 50:
        player_rel['relationship_type'] = "friend"
    elif affinity >= 0:
        player_rel['relationship_type'] = "acquaintance"
    elif affinity >= -50:
        player_rel['relationship_type'] = "stranger"
    else:
        player_rel['relationship_type'] = "enemy"

    # 添加记忆
    memories = npc.setdefault('memories', [])
    turn_number = state.get('turn_number', 0)
    memories.append({
        "turn_number": turn_number,
        "event_type": "relationship_change",
        "summary": f"关系变化: 好感度{affinity_delta:+d}, 信任度{trust_delta:+d}. {reason}",
        "emotional_impact": affinity_delta
    })

    # 保存状态
    state_manager.save_state(current_session_id, state)

    return {
        "success": True,
        "npc_id": npc_id,
        "npc_name": npc.get('name'),
        "affinity": player_rel['affinity'],
        "trust": player_rel['trust'],
        "relationship_type": player_rel['relationship_type'],
        "changes": {
            "affinity": f"{old_affinity:+d} → {player_rel['affinity']:+d}",
            "trust": f"{old_trust} → {player_rel['trust']}"
        },
        "message": f"与 {npc.get('name')} 的关系更新为: {player_rel['relationship_type']}"
    }


@tool(
    "add_npc_memory",
    "为 NPC 添加记忆",
    {
        "type": "object",
        "properties": {
            "npc_id": {"type": "string", "description": "NPC ID"},
            "event_type": {
                "type": "string",
                "description": "事件类型",
                "enum": ["conversation", "quest", "combat", "observation"]
            },
            "summary": {"type": "string", "description": "记忆摘要"},
            "emotional_impact": {
                "type": "integer",
                "description": "情感影响（-10到+10）",
                "default": 0
            }
        },
        "required": ["npc_id", "event_type", "summary"]
    }
)
async def add_npc_memory(args: Dict) -> Dict[str, Any]:
    """为 NPC 添加记忆"""
    npc_id = args['npc_id']
    event_type = args['event_type']
    summary = args['summary']
    emotional_impact = args.get('emotional_impact', 0)

    state = state_manager.get_state(current_session_id)
    npcs = state.get('npcs', [])

    # 查找 NPC
    npc = next((n for n in npcs if n.get('id') == npc_id), None)

    if not npc:
        return {
            "success": False,
            "message": f"NPC {npc_id} 不存在"
        }

    # 添加记忆
    memories = npc.setdefault('memories', [])
    turn_number = state.get('turn_number', 0)

    memories.append({
        "turn_number": turn_number,
        "event_type": event_type,
        "summary": summary,
        "emotional_impact": emotional_impact,
        "participants": ["player"]
    })

    # 保留最近50条记忆
    if len(memories) > 50:
        npc['memories'] = memories[-50:]

    # 保存状态
    state_manager.save_state(current_session_id, state)

    return {
        "success": True,
        "npc_id": npc_id,
        "npc_name": npc.get('name'),
        "memory_count": len(npc['memories']),
        "message": f"为 {npc.get('name')} 添加了记忆"
    }


@tool(
    "save_game",
    "保存游戏到存档槽位",
    {
        "type": "object",
        "properties": {
            "slot_id": {"type": "integer", "minimum": 1, "maximum": 10},
            "save_name": {"type": "string"}
        },
        "required": ["slot_id", "save_name"]
    }
)
async def save_game(args: Dict) -> Dict[str, Any]:
    """保存游戏

    这个工具将当前游戏状态保存到指定存档槽位
    """
    slot_id = args['slot_id']
    save_name = args['save_name']

    # 获取当前游戏状态
    state = state_manager.get_state(current_session_id)

    # 保存到存档表
    if state_manager.db:
        save_id = state_manager.db.save_to_slot(
            user_id="default_user",
            slot_id=slot_id,
            save_name=save_name,
            game_state=state
        )
    else:
        save_id = f"save_{slot_id}"

    return {
        "success": True,
        "save_id": save_id,
        "slot_id": slot_id,
        "save_name": save_name,
        "message": "游戏保存成功"
    }


# ============= 导出所有工具 =============

ALL_GAME_TOOLS = [
    get_player_state,
    add_item,
    update_hp,
    roll_check,
    set_location,
    create_quest,
    get_quests,
    activate_quest,
    update_quest_objective,
    complete_quest,
    create_npc,
    get_npcs,
    update_npc_relationship,
    add_npc_memory,
    save_game
]
