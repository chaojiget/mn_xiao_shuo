"""
游戏工具系统 - LangChain 1.0 实现
从 Claude Agent SDK 迁移到 LangChain
"""

from typing import Dict, Any
from langchain.tools import tool
from langchain_core.tools import ToolException
import random
import contextvars

# ============= 游戏状态管理 =============

# 全局游戏状态（实际应从数据库或session获取）
_game_states: Dict[str, Dict[str, Any]] = {}

# 使用 contextvars 管理当前会话ID（线程安全）
current_session_context = contextvars.ContextVar('current_session_id', default='default')


def get_current_session_id() -> str:
    """获取当前会话ID"""
    return current_session_context.get()


def set_current_session_id(session_id: str):
    """设置当前会话ID"""
    current_session_context.set(session_id)


class GameStateManager:
    """游戏状态管理器 - 处理数据库访问"""

    def __init__(self, db_connection=None):
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
                "gold": 0,
                "exp": 0
            },
            "world": {
                "current_location": "起始村庄",
                "theme": "奇幻世界"
            },
            "turn_number": 0,
            "logs": [],
            "quests": [],
            "npcs": []
        }
        _game_states[session_id] = state
        return state


# 全局状态管理器实例（在应用启动时初始化）
state_manager: GameStateManager = GameStateManager()


def init_state_manager(db_connection):
    """初始化状态管理器"""
    global state_manager
    state_manager = GameStateManager(db_connection)


# ============= LangChain 工具定义 =============

@tool
def get_player_state() -> Dict[str, Any]:
    """获取玩家当前状态（HP、背包、位置等）

    Returns:
        包含玩家状态的字典
    """
    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)
    player = state.get('player', {})

    return {
        "hp": player.get('hp', 100),
        "max_hp": player.get('max_hp', 100),
        "stamina": player.get('stamina', 100),
        "location": state.get('world', {}).get('current_location'),
        "inventory": player.get('inventory', []),
        "gold": player.get('gold', 0)
    }


@tool
def add_item(item_id: str, quantity: int = 1) -> Dict[str, Any]:
    """向玩家背包添加物品

    Args:
        item_id: 物品ID
        quantity: 数量，默认为1

    Returns:
        操作结果
    """
    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)
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
    state_manager.save_state(session_id, state)

    return {
        "success": True,
        "message": f"获得了 {quantity} 个 {item_id}",
        "current_inventory": inventory
    }


@tool
def update_hp(change: int, reason: str = "") -> Dict[str, Any]:
    """更新玩家HP

    Args:
        change: HP变化量（正数为恢复，负数为伤害）
        reason: 原因描述

    Returns:
        HP更新结果
    """
    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)
    player = state.setdefault('player', {})

    old_hp = player.get('hp', 100)
    max_hp = player.get('max_hp', 100)

    new_hp = max(0, min(max_hp, old_hp + change))
    player['hp'] = new_hp

    # 记录日志
    logs = state.setdefault('logs', [])
    logs.append(f"HP变化: {old_hp} → {new_hp} ({reason})")

    # 保存到数据库
    state_manager.save_state(session_id, state)

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


@tool
def roll_check(skill: str, dc: int, modifier: int = 0, advantage: bool = False) -> Dict[str, Any]:
    """进行技能检定（d20系统）

    Args:
        skill: 技能名称（如：力量、敏捷、感知）
        dc: 难度等级（DC）
        modifier: 修正值，默认为0
        advantage: 是否有优势，默认为False

    Returns:
        检定结果
    """
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
    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)
    logs = state.setdefault('logs', [])
    logs.append(f"{skill}检定: {total} vs DC{dc} ({'成功' if success else '失败'})")
    state_manager.save_state(session_id, state)

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


@tool
def set_location(location_id: str, description: str = "") -> Dict[str, Any]:
    """设置玩家位置

    Args:
        location_id: 位置ID
        description: 位置描述

    Returns:
        位置更新结果
    """
    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)
    world = state.setdefault('world', {})

    old_location = world.get('current_location', '未知')
    world['current_location'] = location_id

    # 记录到日志
    logs = state.setdefault('logs', [])
    logs.append(f"从 {old_location} 移动到 {location_id}")

    # 保存到数据库
    state_manager.save_state(session_id, state)

    return {
        "success": True,
        "old_location": old_location,
        "new_location": location_id,
        "description": description
    }


@tool
def create_quest(title: str, description: str, objectives: list, rewards: dict,
                 quest_type: str = "main", level_requirement: int = 1) -> Dict[str, Any]:
    """创建新任务

    Args:
        title: 任务标题
        description: 任务描述
        objectives: 任务目标列表
        rewards: 任务奖励字典
        quest_type: 任务类型，默认为"main"
        level_requirement: 等级要求，默认为1

    Returns:
        任务创建结果
    """
    session_id = get_current_session_id()
    quest_id = f"quest_{random.randint(1000, 9999)}"

    quest_data = {
        "id": quest_id,
        "type": quest_type,
        "title": title,
        "description": description,
        "level_requirement": level_requirement,
        "objectives": objectives,
        "rewards": rewards,
        "status": "available"
    }

    # 添加到游戏状态
    state = state_manager.get_state(session_id)
    quests = state.setdefault('quests', [])
    quests.append(quest_data)
    state_manager.save_state(session_id, state)

    return {
        "success": True,
        "quest_id": quest_id,
        "message": f"任务 '{title}' 创建成功"
    }


@tool
def get_quests(status: str = None) -> Dict[str, Any]:
    """获取任务列表

    Args:
        status: 任务状态筛选（available/active/completed/failed），不传则返回所有

    Returns:
        任务列表
    """
    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)
    all_quests = state.get('quests', [])

    # 筛选状态
    if status:
        filtered_quests = [q for q in all_quests if q.get('status') == status]
    else:
        filtered_quests = all_quests

    return {
        "quests": filtered_quests,
        "count": len(filtered_quests),
        "total": len(all_quests)
    }


@tool
def activate_quest(quest_id: str) -> Dict[str, Any]:
    """激活任务（从available变为active）

    Args:
        quest_id: 任务ID

    Returns:
        激活结果
    """
    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)
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
    state_manager.save_state(session_id, state)

    return {
        "success": True,
        "quest_id": quest_id,
        "message": f"任务 '{quest.get('title')}' 已激活"
    }


@tool
def update_quest_objective(quest_id: str, objective_id: str, amount: int = 1) -> Dict[str, Any]:
    """更新任务目标进度

    Args:
        quest_id: 任务ID
        objective_id: 目标ID
        amount: 进度增加量，默认为1

    Returns:
        更新结果
    """
    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)
    quests = state.get('quests', [])

    # 查找任务
    quest = next((q for q in quests if q.get('id') == quest_id), None)
    if not quest:
        return {"success": False, "message": f"任务 {quest_id} 不存在"}

    # 查找目标
    objectives = quest.get('objectives', [])
    objective = next((obj for obj in objectives if obj.get('id') == objective_id), None)
    if not objective:
        return {"success": False, "message": f"目标 {objective_id} 不存在"}

    # 更新进度
    current = objective.get('current', 0)
    required = objective.get('required', 1)
    new_current = min(current + amount, required)
    objective['current'] = new_current
    objective['completed'] = new_current >= required

    state_manager.save_state(session_id, state)

    return {
        "success": True,
        "quest_id": quest_id,
        "objective_id": objective_id,
        "current": new_current,
        "required": required,
        "completed": objective['completed'],
        "message": f"目标进度: {new_current}/{required}"
    }


@tool
def complete_quest(quest_id: str) -> Dict[str, Any]:
    """完成任务并发放奖励

    Args:
        quest_id: 任务ID

    Returns:
        完成结果
    """
    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)
    quests = state.get('quests', [])

    # 查找任务
    quest = next((q for q in quests if q.get('id') == quest_id), None)
    if not quest:
        return {"success": False, "message": f"任务 {quest_id} 不存在"}

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
        player['exp'] = player.get('exp', 0) + exp_reward

    # 金币
    gold_reward = rewards.get('gold', 0)
    if gold_reward > 0:
        player['gold'] = player.get('gold', 0) + gold_reward

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
    state_manager.save_state(session_id, state)

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


@tool
def create_npc(npc_id: str, name: str, role: str, location: str,
               description: str = "", personality_traits: list = None,
               speech_style: str = "", goals: list = None) -> Dict[str, Any]:
    """创建新的 NPC

    Args:
        npc_id: NPC唯一ID
        name: NPC名字
        role: 职业/角色
        location: 当前位置
        description: 外貌和背景描述
        personality_traits: 性格特征列表
        speech_style: 说话风格
        goals: 目标列表

    Returns:
        NPC创建结果
    """
    session_id = get_current_session_id()

    npc_data = {
        "id": npc_id,
        "name": name,
        "role": role,
        "description": description,
        "status": "active",
        "current_location": location,
        "personality": {
            "traits": personality_traits or [],
            "speech_style": speech_style
        },
        "goals": goals or [],
        "memories": [],
        "relationships": [],
        "available_quests": []
    }

    # 保存到游戏状态
    state = state_manager.get_state(session_id)
    npcs = state.setdefault('npcs', [])
    npcs.append(npc_data)
    state_manager.save_state(session_id, state)

    return {
        "success": True,
        "npc_id": npc_id,
        "name": name,
        "message": f"NPC '{name}' 创建成功，位于 {location}"
    }


@tool
def get_npcs(location: str = None, status: str = None) -> Dict[str, Any]:
    """获取 NPC 列表

    Args:
        location: 位置筛选，不传则返回所有NPC
        status: 状态筛选（active/inactive/retired）

    Returns:
        NPC列表
    """
    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)
    all_npcs = state.get('npcs', [])

    # 筛选位置
    filtered_npcs = all_npcs
    if location:
        filtered_npcs = [n for n in filtered_npcs if n.get('current_location') == location]

    # 筛选状态
    if status:
        filtered_npcs = [n for n in filtered_npcs if n.get('status') == status]

    return {
        "npcs": filtered_npcs,
        "count": len(filtered_npcs),
        "total": len(all_npcs),
        "location": location
    }


@tool
def update_npc_relationship(npc_id: str, affinity_delta: int = 0,
                           trust_delta: int = 0, reason: str = "") -> Dict[str, Any]:
    """更新 NPC 与玩家的关系

    Args:
        npc_id: NPC ID
        affinity_delta: 好感度变化（-100到+100）
        trust_delta: 信任度变化（0到100）
        reason: 原因描述

    Returns:
        关系更新结果
    """
    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)
    npcs = state.get('npcs', [])

    # 查找 NPC
    npc = next((n for n in npcs if n.get('id') == npc_id), None)
    if not npc:
        return {"success": False, "message": f"NPC {npc_id} 不存在"}

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

    state_manager.save_state(session_id, state)

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


@tool
def add_npc_memory(npc_id: str, event_type: str, summary: str,
                   emotional_impact: int = 0) -> Dict[str, Any]:
    """为 NPC 添加记忆

    Args:
        npc_id: NPC ID
        event_type: 事件类型（conversation/quest/combat/observation）
        summary: 记忆摘要
        emotional_impact: 情感影响（-10到+10）

    Returns:
        记忆添加结果
    """
    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)
    npcs = state.get('npcs', [])

    # 查找 NPC
    npc = next((n for n in npcs if n.get('id') == npc_id), None)
    if not npc:
        return {"success": False, "message": f"NPC {npc_id} 不存在"}

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

    state_manager.save_state(session_id, state)

    return {
        "success": True,
        "npc_id": npc_id,
        "npc_name": npc.get('name'),
        "memory_count": len(npc['memories']),
        "message": f"为 {npc.get('name')} 添加了记忆"
    }


@tool
def save_game(slot_id: int, save_name: str) -> Dict[str, Any]:
    """保存游戏到存档槽位

    Args:
        slot_id: 存档槽位（1-10）
        save_name: 存档名称

    Returns:
        保存结果
    """
    if not (1 <= slot_id <= 10):
        return {"success": False, "message": "存档槽位必须在 1-10 之间"}

    session_id = get_current_session_id()
    state = state_manager.get_state(session_id)

    # 保存到存档表（如果有数据库）
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
