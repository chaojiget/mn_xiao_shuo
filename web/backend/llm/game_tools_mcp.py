"""
游戏工具 MCP Server

为 Claude Agent SDK 提供游戏专用的工具,包括:
- 投骰子 (roll_dice)
- 检定判定 (skill_check)
- 更新玩家状态 (update_player)
- 添加物品 (add_item)
- 移除物品 (remove_item)
- 解锁地点 (unlock_location)
- 设置标记 (set_flag)

这些工具可以让 Agent 直接操作游戏状态
"""

import random
from typing import Any, Dict, Optional

from claude_agent_sdk import create_sdk_mcp_server, tool
from utils.logger import get_logger

logger = get_logger(__name__)

# ========================================
# 骰子和检定工具
# ========================================

@tool(
    "roll_dice",
    "投骰子 - 生成随机数用于游戏判定",
    {
        "sides": {"type": "integer", "description": "骰子面数(如6面骰、20面骰等)"},
        "count": {"type": "integer", "description": "投掷次数", "default": 1},
        "modifier": {"type": "integer", "description": "修正值(加减)", "default": 0}
    }
)
async def roll_dice(args):
    """投骰子工具"""
    sides = args["sides"]
    count = args.get("count", 1)
    modifier = args.get("modifier", 0)

    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls) + modifier

    result_text = f"投掷 {count}d{sides}"
    if modifier != 0:
        result_text += f"{modifier:+d}"
    result_text += f"\n结果: {rolls}"
    if modifier != 0:
        result_text += f" {modifier:+d}"
    result_text += f" = {total}"

    return {
        "content": [
            {
                "type": "text",
                "text": result_text
            }
        ],
        "metadata": {
            "rolls": rolls,
            "modifier": modifier,
            "total": total
        }
    }


@tool(
    "skill_check",
    "技能检定 - 检查玩家是否通过某个挑战",
    {
        "skill_name": {"type": "string", "description": "技能名称(如'力量''敏捷''智力'等)"},
        "difficulty": {"type": "integer", "description": "难度值(DC,10-30)"},
        "player_bonus": {"type": "integer", "description": "玩家加值", "default": 0}
    }
)
async def skill_check(args):
    """技能检定工具"""
    skill_name = args["skill_name"]
    difficulty = args["difficulty"]
    player_bonus = args.get("player_bonus", 0)

    # 投d20
    roll = random.randint(1, 20)
    total = roll + player_bonus
    success = total >= difficulty

    # 判定结果
    if roll == 1:
        result_type = "大失败"
        success = False
    elif roll == 20:
        result_type = "大成功"
        success = True
    elif success:
        result_type = "成功"
    else:
        result_type = "失败"

    result_text = f"【{skill_name}检定】\n"
    result_text += f"难度: DC {difficulty}\n"
    result_text += f"投掷: d20={roll}"
    if player_bonus != 0:
        result_text += f" {player_bonus:+d}"
    result_text += f" = {total}\n"
    result_text += f"结果: {result_type}"

    return {
        "content": [
            {
                "type": "text",
                "text": result_text
            }
        ],
        "metadata": {
            "skill": skill_name,
            "roll": roll,
            "bonus": player_bonus,
            "total": total,
            "difficulty": difficulty,
            "success": success,
            "result_type": result_type
        }
    }


# ========================================
# 玩家状态管理工具
# ========================================

@tool(
    "update_player_hp",
    "更新玩家生命值",
    {
        "change": {"type": "integer", "description": "生命值变化(正数为恢复,负数为伤害)"},
        "reason": {"type": "string", "description": "变化原因(如'受到攻击''使用治疗药水'等)"}
    }
)
async def update_player_hp(args):
    """更新玩家生命值"""
    change = args["change"]
    reason = args["reason"]

    # 注意: 这里返回的是指令,实际更新由游戏引擎执行
    if change > 0:
        action = "恢复"
        text = f"生命值{action} {abs(change)} 点 ({reason})"
    else:
        action = "损失"
        text = f"生命值{action} {abs(change)} 点 ({reason})"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "update_hp",
            "change": change,
            "reason": reason
        }
    }


@tool(
    "update_player_stamina",
    "更新玩家体力值",
    {
        "change": {"type": "integer", "description": "体力值变化"},
        "reason": {"type": "string", "description": "变化原因"}
    }
)
async def update_player_stamina(args):
    """更新玩家体力值"""
    change = args["change"]
    reason = args["reason"]

    if change > 0:
        action = "恢复"
    else:
        action = "消耗"

    text = f"体力{action} {abs(change)} 点 ({reason})"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "update_stamina",
            "change": change,
            "reason": reason
        }
    }


# ========================================
# 物品管理工具
# ========================================

@tool(
    "check_inventory",
    "查看玩家背包 - 显示当前携带的所有物品",
    {}
)
async def check_inventory(args):
    """查看背包"""
    # 这个工具会返回指令,让游戏引擎返回实际的背包内容
    text = "📦 查看背包"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "check_inventory",
            "action": "query_inventory"
        }
    }


@tool(
    "use_item",
    "使用背包中的物品",
    {
        "item_id": {"type": "string", "description": "物品ID"},
        "target": {"type": "string", "description": "使用目标(如'self'/'enemy'等)", "default": "self"}
    }
)
async def use_item(args):
    """使用物品"""
    item_id = args["item_id"]
    target = args.get("target", "self")

    text = f"使用物品: {item_id} (目标: {target})"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "use_item",
            "item_id": item_id,
            "target": target
        }
    }


@tool(
    "add_item",
    "添加物品到玩家背包",
    {
        "item_id": {"type": "string", "description": "物品ID"},
        "item_name": {"type": "string", "description": "物品名称"},
        "quantity": {"type": "integer", "description": "数量", "default": 1},
        "description": {"type": "string", "description": "物品描述", "default": ""}
    }
)
async def add_item(args):
    """添加物品"""
    item_name = args["item_name"]
    quantity = args.get("quantity", 1)

    text = f"获得物品: {item_name} x{quantity}"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "add_item",
            "item_id": args["item_id"],
            "item_name": item_name,
            "quantity": quantity,
            "description": args.get("description", "")
        }
    }


@tool(
    "remove_item",
    "从玩家背包移除物品",
    {
        "item_id": {"type": "string", "description": "物品ID"},
        "quantity": {"type": "integer", "description": "数量", "default": 1}
    }
)
async def remove_item(args):
    """移除物品"""
    item_id = args["item_id"]
    quantity = args.get("quantity", 1)

    text = f"失去物品: {item_id} x{quantity}"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "remove_item",
            "item_id": item_id,
            "quantity": quantity
        }
    }


# ========================================
# 地图和探索工具
# ========================================

@tool(
    "check_map",
    "查看地图 - 显示已发现的地点和可前往的路径",
    {}
)
async def check_map(args):
    """查看地图"""
    text = "🗺️ 查看地图"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "check_map",
            "action": "query_map"
        }
    }


@tool(
    "check_surroundings",
    "环顾四周 - 查看当前位置的详细描述和可互动对象",
    {}
)
async def check_surroundings(args):
    """环顾四周"""
    text = "👀 环顾四周"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "check_surroundings",
            "action": "describe_location"
        }
    }


@tool(
    "unlock_location",
    "解锁新地点",
    {
        "location_id": {"type": "string", "description": "地点ID"},
        "location_name": {"type": "string", "description": "地点名称"},
        "description": {"type": "string", "description": "地点描述", "default": ""}
    }
)
async def unlock_location(args):
    """解锁新地点"""
    location_name = args["location_name"]

    text = f"🗺️ 解锁新地点: {location_name}"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "unlock_location",
            "location_id": args["location_id"],
            "location_name": location_name,
            "description": args.get("description", "")
        }
    }


@tool(
    "set_location",
    "设置玩家当前位置",
    {
        "location_id": {"type": "string", "description": "地点ID"}
    }
)
async def set_location(args):
    """设置玩家位置"""
    location_id = args["location_id"]

    text = f"移动到: {location_id}"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "set_location",
            "location_id": location_id
        }
    }


# ========================================
# 玩家状态查询工具
# ========================================

@tool(
    "check_status",
    "查看玩家状态 - 显示生命值、体力、等级等信息",
    {}
)
async def check_status(args):
    """查看玩家状态"""
    text = "📊 查看角色状态"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "check_status",
            "action": "query_player_stats"
        }
    }


@tool(
    "check_quests",
    "查看任务列表 - 显示当前所有任务的状态",
    {}
)
async def check_quests(args):
    """查看任务列表"""
    text = "📜 查看任务"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "check_quests",
            "action": "query_quests"
        }
    }


# ========================================
# 标记和状态工具
# ========================================

@tool(
    "set_flag",
    "设置游戏标记(用于剧情进度追踪)",
    {
        "flag_name": {"type": "string", "description": "标记名称"},
        "value": {"type": "boolean", "description": "标记值(true/false)", "default": True}
    }
)
async def set_flag(args):
    """设置游戏标记"""
    flag_name = args["flag_name"]
    value = args.get("value", True)

    text = f"设置标记: {flag_name} = {value}"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "set_flag",
            "flag_name": flag_name,
            "value": value
        }
    }


@tool(
    "award_experience",
    "奖励经验值",
    {
        "amount": {"type": "integer", "description": "经验值数量"},
        "reason": {"type": "string", "description": "奖励原因"}
    }
)
async def award_experience(args):
    """奖励经验值"""
    amount = args["amount"]
    reason = args["reason"]

    text = f"💫 获得 {amount} 点经验 ({reason})"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "award_experience",
            "amount": amount,
            "reason": reason
        }
    }


# ========================================
# NPC 交互工具
# ========================================

@tool(
    "talk_to_npc",
    "与NPC对话",
    {
        "npc_id": {"type": "string", "description": "NPC ID"},
        "topic": {"type": "string", "description": "对话话题", "default": ""}
    }
)
async def talk_to_npc(args):
    """与NPC对话"""
    npc_id = args["npc_id"]
    topic = args.get("topic", "")

    if topic:
        text = f"💬 与 {npc_id} 对话 (话题: {topic})"
    else:
        text = f"💬 与 {npc_id} 对话"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "talk_to_npc",
            "npc_id": npc_id,
            "topic": topic
        }
    }


@tool(
    "trade_with_npc",
    "与NPC交易",
    {
        "npc_id": {"type": "string", "description": "NPC ID"},
        "action": {"type": "string", "description": "交易动作(buy/sell)"},
        "item_id": {"type": "string", "description": "物品ID"},
        "quantity": {"type": "integer", "description": "数量", "default": 1}
    }
)
async def trade_with_npc(args):
    """与NPC交易"""
    npc_id = args["npc_id"]
    action = args["action"]
    item_id = args["item_id"]
    quantity = args.get("quantity", 1)

    action_cn = "购买" if action == "buy" else "出售"
    text = f"💰 {action_cn} {item_id} x{quantity} (NPC: {npc_id})"

    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "metadata": {
            "tool_name": "trade_with_npc",
            "npc_id": npc_id,
            "action": action,
            "item_id": item_id,
            "quantity": quantity
        }
    }


# ========================================
# 创建 MCP Server
# ========================================

def create_game_tools_server():
    """
    创建游戏工具 MCP Server

    Returns:
        MCP Server 实例,可以传递给 ClaudeAgentOptions
    """
    return create_sdk_mcp_server(
        name="game-tools",
        version="1.0.0",
        tools=[
            # 骰子和检定
            roll_dice,
            skill_check,

            # 玩家状态
            update_player_hp,
            update_player_stamina,
            check_status,

            # 物品管理
            check_inventory,
            use_item,
            add_item,
            remove_item,

            # 地图探索
            check_map,
            check_surroundings,
            unlock_location,
            set_location,

            # 任务系统
            check_quests,

            # NPC 交互
            talk_to_npc,
            trade_with_npc,

            # 标记和奖励
            set_flag,
            award_experience
        ]
    )


# 便捷函数:获取工具名称列表
def get_game_tool_names():
    """
    获取所有游戏工具的名称列表

    Returns:
        List[str]: 工具名称列表,格式为 "mcp__game-tools__<tool_name>"

    使用示例:
        allowed_tools = get_game_tool_names()
        opts = ClaudeAgentOptions(allowed_tools=allowed_tools)
    """
    tool_names = [
        # 骰子和检定
        "roll_dice",
        "skill_check",

        # 玩家状态
        "update_player_hp",
        "update_player_stamina",
        "check_status",

        # 物品管理
        "check_inventory",
        "use_item",
        "add_item",
        "remove_item",

        # 地图探索
        "check_map",
        "check_surroundings",
        "unlock_location",
        "set_location",

        # 任务系统
        "check_quests",

        # NPC 交互
        "talk_to_npc",
        "trade_with_npc",

        # 标记和奖励
        "set_flag",
        "award_experience"
    ]

    return [f"mcp__game-tools__{name}" for name in tool_names]


# 使用示例
if __name__ == "__main__":
    import anyio
    from claude_agent_sdk import query, ClaudeAgentOptions

    async def test_game_tools():
        # 创建游戏工具 server
        game_tools = create_game_tools_server()

        # 配置 Agent
        opts = ClaudeAgentOptions(
            mcp_servers={"game-tools": game_tools},
            allowed_tools=get_game_tool_names(),
            max_turns=3
        )

        # 测试工具调用
        async for msg in query(
            prompt="帮我投一个20面骰子,然后进行一次敏捷检定(难度15,玩家加值+3)",
            options=opts
        ):
            logger.info(msg)

    anyio.run(test_game_tools())
