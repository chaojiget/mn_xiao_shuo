"""
测试WorldPack到冒险的完整流程
"""
import requests
import json

def test_world_to_adventure():
    """测试从WorldPack加载并开始冒险"""

    print("=" * 80)
    print("🎮 测试WorldPack到冒险流程")
    print("=" * 80)

    # 1. 列出所有世界
    print("\n📋 步骤1: 列出所有世界")
    response = requests.get("http://localhost:8000/api/worlds")
    result = response.json()

    # 处理返回的数据结构
    if isinstance(result, dict) and "worlds" in result:
        worlds = result["worlds"]
    elif isinstance(result, list):
        worlds = result
    else:
        print(f"❌ 未知的返回格式: {result}")
        return False

    if not worlds:
        print("❌ 没有找到任何世界，请先生成一个世界")
        return False

    world = worlds[0]
    world_id = world["id"]
    world_title = world["title"]

    print(f"✅ 找到世界: {world_title} (ID: {world_id})")

    # 2. 初始化游戏
    print(f"\n🚀 步骤2: 使用世界 {world_id} 初始化游戏")
    response = requests.post(
        "http://localhost:8000/api/game/init",
        headers={"Content-Type": "application/json"},
        json={"worldId": world_id}
    )

    if response.status_code != 200:
        print(f"❌ 初始化失败: {response.text}")
        return False

    data = response.json()

    if not data.get("success"):
        print(f"❌ 初始化失败: {data}")
        return False

    print("✅ 游戏初始化成功！")

    # 3. 验证返回数据
    print("\n📊 步骤3: 验证返回数据")

    state = data["state"]
    narration = data["narration"]
    suggestions = data["suggestions"]

    print(f"\n📖 开场白:")
    print(f"   {narration}")

    print(f"\n💡 建议行动:")
    for suggestion in suggestions:
        print(f"   - {suggestion}")

    print(f"\n👤 玩家状态:")
    player = state["player"]
    print(f"   HP: {player['hp']}/{player['maxHp']}")
    print(f"   体力: {player['stamina']}/{player['maxStamina']}")
    print(f"   位置: {player['location']}")
    print(f"   背包物品: {len(player['inventory'])}")

    print(f"\n🗺️ 地图:")
    game_map = state["map"]
    print(f"   地点数: {len(game_map['nodes'])}")
    print(f"   连接数: {len(game_map['edges'])}")
    print(f"   当前节点: {game_map['currentNodeId']}")

    discovered = [n for n in game_map['nodes'] if n['discovered']]
    print(f"   已发现: {len(discovered)}/{len(game_map['nodes'])}")

    print(f"\n📜 任务:")
    quests = state["quests"]
    active_quests = [q for q in quests if q['status'] == 'active']
    print(f"   总任务数: {len(quests)}")
    print(f"   激活任务: {len(active_quests)}")

    if active_quests:
        quest = active_quests[0]
        print(f"\n   当前主线任务: {quest['title']}")
        print(f"   描述: {quest['description']}")
        print(f"   目标数: {len(quest['objectives'])}")

    print(f"\n🌍 世界状态:")
    world_state = state["world"]
    print(f"   主题: {world_state.get('theme', 'N/A')}")
    print(f"   已发现地点: {len(world_state['discoveredLocations'])}")

    variables = world_state.get('variables', {})
    print(f"   世界ID: {variables.get('world_pack_id', 'N/A')}")
    print(f"   世界标题: {variables.get('world_pack_title', 'N/A')}")
    print(f"   基调: {variables.get('world_tone', 'N/A')}")
    print(f"   难度: {variables.get('world_difficulty', 'N/A')}")

    # 4. 验证数据一致性
    print("\n🔍 步骤4: 验证数据一致性")

    checks = []

    # 检查地点数
    if len(game_map['nodes']) > 0:
        checks.append("✅ 地图有地点")
    else:
        checks.append("❌ 地图没有地点")

    # 检查任务
    if len(quests) > 0:
        checks.append("✅ 有任务")
    else:
        checks.append("❌ 没有任务")

    # 检查至少有一个激活任务
    if len(active_quests) > 0:
        checks.append("✅ 有激活的任务")
    else:
        checks.append("⚠️ 没有激活的任务")

    # 检查玩家位置在地图中
    player_loc = player['location']
    node_ids = [n['id'] for n in game_map['nodes']]
    if player_loc in node_ids:
        checks.append("✅ 玩家位置在地图中")
    else:
        checks.append("❌ 玩家位置不在地图中")

    # 检查至少有一个已发现地点
    if len(discovered) > 0:
        checks.append("✅ 至少有一个已发现地点")
    else:
        checks.append("❌ 没有已发现地点")

    # 检查元数据
    if state.get('metadata', {}).get('worldPackId') == world_id:
        checks.append("✅ 元数据worldPackId正确")
    else:
        checks.append("❌ 元数据worldPackId不正确")

    for check in checks:
        print(f"   {check}")

    all_passed = all("✅" in check for check in checks)

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ 所有测试通过！WorldPack到冒险流程正常工作！")
        print("=" * 80)
        return True
    else:
        print("⚠️ 部分测试未通过，请检查上述问题")
        print("=" * 80)
        return False


if __name__ == "__main__":
    import sys
    success = test_world_to_adventure()
    sys.exit(0 if success else 1)
