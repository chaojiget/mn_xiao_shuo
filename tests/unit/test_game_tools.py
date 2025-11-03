"""
游戏工具单元测试
测试 game_tools.py 中的所有工具函数
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "web" / "backend"))

from game.game_tools import (
    GameTools,
    GameState,
    PlayerState,
    WorldState,
    GameMap,
    MapNode,
    Quest,
    InventoryItem
)


@pytest.fixture
def sample_game_state():
    """创建测试用的游戏状态"""
    player = PlayerState(
        hp=100,
        maxHp=100,
        stamina=100,
        maxStamina=100,
        traits=["勇敢"],
        inventory=[],
        location="village",
        money=50
    )

    world = WorldState(
        time=0,
        flags={},
        discoveredLocations=["village"],
        variables={},
        currentScene=None
    )

    game_map = GameMap(
        nodes=[
            MapNode(
                id="village",
                name="新手村",
                shortDesc="一个宁静的小村庄",
                discovered=True,
                locked=False
            ),
            MapNode(
                id="forest",
                name="黑暗森林",
                shortDesc="危险的森林",
                discovered=False,
                locked=False
            )
        ],
        edges=[],
        currentNodeId="village"
    )

    state = GameState(
        version="1.0.0",
        player=player,
        world=world,
        quests=[],
        map=game_map,
        log=[]
    )

    return state


@pytest.fixture
def game_tools(sample_game_state):
    """创建GameTools实例"""
    return GameTools(sample_game_state)


# ==================== 状态读取测试 ====================

def test_get_player_state(game_tools):
    """测试获取玩家状态"""
    player = game_tools.get_player_state()
    assert player.hp == 100
    assert player.location == "village"
    assert player.money == 50


def test_get_world_state(game_tools):
    """测试获取世界状态"""
    world = game_tools.get_world_state()
    assert world.time == 0
    assert "village" in world.discoveredLocations


def test_get_location(game_tools):
    """测试获取位置信息"""
    location = game_tools.get_location("village")
    assert location is not None
    assert location.name == "新手村"
    assert location.discovered is True


# ==================== 背包管理测试 ====================

def test_add_item(game_tools):
    """测试添加物品"""
    result = game_tools.add_item(
        item_id="sword",
        name="铁剑",
        quantity=1,
        description="一把普通的铁剑",
        type="weapon"
    )

    assert result is True
    assert len(game_tools.state.player.inventory) == 1
    assert game_tools.state.player.inventory[0].id == "sword"


def test_add_item_stack(game_tools):
    """测试物品堆叠"""
    game_tools.add_item(item_id="potion", name="药水", quantity=2)
    game_tools.add_item(item_id="potion", name="药水", quantity=3)

    item = game_tools.get_inventory_item("potion")
    assert item is not None
    assert item.quantity == 5


def test_remove_item(game_tools):
    """测试移除物品"""
    game_tools.add_item(item_id="coin", name="金币", quantity=10)
    result = game_tools.remove_item("coin", 3)

    assert result is True
    item = game_tools.get_inventory_item("coin")
    assert item.quantity == 7


def test_remove_item_all(game_tools):
    """测试移除全部物品"""
    game_tools.add_item(item_id="key", name="钥匙", quantity=1)
    result = game_tools.remove_item("key", 1)

    assert result is True
    assert len(game_tools.state.player.inventory) == 0


def test_remove_nonexistent_item(game_tools):
    """测试移除不存在的物品"""
    result = game_tools.remove_item("phantom_item", 1)
    assert result is False


# ==================== 生命值和体力测试 ====================

def test_update_hp_damage(game_tools):
    """测试扣除生命值"""
    new_hp = game_tools.update_hp(-30)
    assert new_hp == 70


def test_update_hp_heal(game_tools):
    """测试恢复生命值"""
    game_tools.update_hp(-50)  # 先扣血到50
    new_hp = game_tools.update_hp(20)
    assert new_hp == 70


def test_update_hp_max_cap(game_tools):
    """测试生命值不能超过上限"""
    new_hp = game_tools.update_hp(200)
    assert new_hp == 100  # 不能超过maxHp


def test_update_hp_death(game_tools):
    """测试生命值不能低于0"""
    new_hp = game_tools.update_hp(-200)
    assert new_hp == 0


def test_update_stamina(game_tools):
    """测试体力更新"""
    new_stamina = game_tools.update_stamina(-40)
    assert new_stamina == 60

    new_stamina = game_tools.update_stamina(20)
    assert new_stamina == 80


# ==================== 位置管理测试 ====================

def test_set_location(game_tools):
    """测试设置位置"""
    result = game_tools.set_location("forest")
    assert result is True
    assert game_tools.state.player.location == "forest"
    assert "forest" in game_tools.state.world.discoveredLocations


def test_set_invalid_location(game_tools):
    """测试设置无效位置"""
    result = game_tools.set_location("nonexistent")
    assert result is False
    assert game_tools.state.player.location == "village"  # 位置不变


def test_discover_location(game_tools):
    """测试发现新地点"""
    result = game_tools.discover_location("forest")
    assert result is True
    assert "forest" in game_tools.state.world.discoveredLocations

    # 再次发现应返回False
    result = game_tools.discover_location("forest")
    assert result is False


# ==================== 标志位测试 ====================

def test_set_and_get_flag(game_tools):
    """测试设置和获取标志位"""
    game_tools.set_flag("quest_completed", True)
    assert game_tools.get_flag("quest_completed") is True

    game_tools.set_flag("enemy_count", 5)
    assert game_tools.get_flag("enemy_count") == 5


def test_get_flag_default(game_tools):
    """测试获取不存在的标志位（返回默认值）"""
    result = game_tools.get_flag("nonexistent", "default")
    assert result == "default"


# ==================== 特质管理测试 ====================

def test_add_trait(game_tools):
    """测试添加特质"""
    result = game_tools.add_trait("力大无穷")
    assert result is True
    assert "力大无穷" in game_tools.state.player.traits


def test_add_duplicate_trait(game_tools):
    """测试添加重复特质"""
    game_tools.add_trait("隐身")
    result = game_tools.add_trait("隐身")
    assert result is False


def test_remove_trait(game_tools):
    """测试移除特质"""
    game_tools.add_trait("飞行")
    result = game_tools.remove_trait("飞行")
    assert result is True
    assert "飞行" not in game_tools.state.player.traits


# ==================== 检定系统测试 ====================

def test_roll_check(game_tools):
    """测试技能检定"""
    result = game_tools.roll_check(
        type="strength",
        dc=15,
        modifier=3
    )

    assert "roll" in result
    assert "total" in result
    assert "success" in result
    assert 1 <= result["roll"] <= 20
    assert result["total"] == result["roll"] + 3


def test_roll_check_with_advantage(game_tools):
    """测试优势检定"""
    # 多次测试以验证优势机制
    results = []
    for _ in range(10):
        result = game_tools.roll_check(
            type="perception",
            dc=10,
            advantage=True
        )
        results.append(result["roll"])

    # 优势检定的平均值应该更高（统计学上）
    assert max(results) >= 10  # 至少有一次高于10


# ==================== 任务系统测试 ====================

def test_create_quest(game_tools):
    """测试创建任务"""
    result = game_tools.create_quest(
        quest_id="quest_001",
        title="寻找失落的宝藏",
        description="前往森林寻找传说中的宝藏",
        objectives=[
            {"id": "obj1", "description": "到达森林"},
            {"id": "obj2", "description": "击败守卫"}
        ]
    )

    assert result is True
    assert len(game_tools.state.quests) == 1
    quest = game_tools.state.quests[0]
    assert quest.id == "quest_001"
    assert quest.status == "active"
    assert len(quest.objectives) == 2


def test_update_quest(game_tools):
    """测试更新任务"""
    game_tools.create_quest("quest_002", "测试任务", "描述")
    result = game_tools.update_quest("quest_002", status="completed")

    assert result is True
    quest = game_tools.state.quests[0]
    assert quest.status == "completed"


def test_complete_quest_with_rewards(game_tools):
    """测试完成任务并获得奖励"""
    game_tools.create_quest("quest_003", "打败史莱姆", "消灭5只史莱姆")

    rewards = {
        "exp": 100,
        "gold": 50,
        "items": [{"id": "sword", "name": "铁剑", "quantity": 1}]
    }

    result = game_tools.complete_quest("quest_003", rewards)

    assert result is True
    quest = game_tools.state.quests[0]
    assert quest.status == "completed"
    assert game_tools.state.player.money == 100  # 50初始 + 50奖励
    assert len(game_tools.state.player.inventory) == 1


# ==================== 经验值和升级测试 ====================

def test_add_exp(game_tools):
    """测试增加经验值"""
    result = game_tools.add_exp(50)

    assert result["new_exp"] == 50
    assert result["leveled_up"] is False


def test_level_up(game_tools):
    """测试升级"""
    # 添加足够的经验值触发升级（100 exp per level）
    result = game_tools.add_exp(150)

    assert result["leveled_up"] is True
    assert result["new_level"] == 2
    assert game_tools.state.player.maxHp > 100  # HP上限应该提升


# ==================== 物品使用测试 ====================

def test_use_consumable_item(game_tools):
    """测试使用消耗品"""
    # 添加一个HP恢复药水
    game_tools.add_item(
        item_id="hp_potion",
        name="生命药水",
        quantity=1,
        type="consumable",
        properties={"effects": {"hp": 30}}
    )

    # 先扣血
    game_tools.update_hp(-50)

    # 使用药水
    result = game_tools.use_item("hp_potion")

    assert result["success"] is True
    assert "恢复 30 HP" in result["effects_applied"]
    assert game_tools.state.player.hp == 80  # 50 + 30
    assert game_tools.get_inventory_item("hp_potion") is None  # 已消耗


def test_use_non_consumable_item(game_tools):
    """测试使用非消耗品"""
    game_tools.add_item(
        item_id="armor",
        name="铁甲",
        type="armor"
    )

    result = game_tools.use_item("armor")
    assert result["success"] is False


# ==================== 战斗系统测试 ====================

def test_roll_attack(game_tools):
    """测试攻击检定"""
    result = game_tools.roll_attack(weapon_bonus=5)

    assert "roll" in result
    assert "total" in result
    assert result["total"] == result["roll"] + 5
    assert 1 <= result["roll"] <= 20


def test_roll_attack_critical(game_tools):
    """测试暴击"""
    # 多次测试以捕获暴击
    found_critical = False
    for _ in range(100):
        result = game_tools.roll_attack()
        if result["critical_hit"]:
            found_critical = True
            assert result["damage_multiplier"] == 2
            break

    # 统计学上，100次中至少有一次暴击的概率很高
    assert found_critical


def test_calculate_damage(game_tools):
    """测试伤害计算"""
    attack_roll = game_tools.roll_attack(weapon_bonus=3)

    # 假设攻击命中（AC=10）
    if attack_roll["total"] >= 10:
        damage_result = game_tools.calculate_damage(
            base_damage=10,
            attack_roll=attack_roll,
            armor_class=10
        )

        assert damage_result["hit"] is True
        assert damage_result["damage"] >= 10  # 至少是基础伤害


# ==================== 日志测试 ====================

def test_add_log(game_tools):
    """测试添加日志"""
    game_tools.add_log("player", "玩家进入了新手村")
    assert len(game_tools.state.log) == 1
    assert game_tools.state.log[0].actor == "player"
    assert "新手村" in game_tools.state.log[0].text


def test_query_memory(game_tools):
    """测试查询记忆"""
    game_tools.add_log("player", "事件1")
    game_tools.add_log("system", "事件2")
    game_tools.add_log("npc", "事件3")

    recent = game_tools.query_memory("test", limit=2)
    assert len(recent) == 2
    assert recent[-1].text == "事件3"


# ==================== 工具定义测试 ====================

def test_get_tool_definitions():
    """测试工具定义格式"""
    tools = GameTools.get_tool_definitions()

    assert len(tools) > 0
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool

    # 验证关键工具存在
    tool_names = [t["name"] for t in tools]
    assert "add_item" in tool_names
    assert "roll_check" in tool_names
    assert "update_hp" in tool_names
    assert "create_quest" in tool_names
    assert "save_game" in tool_names


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
