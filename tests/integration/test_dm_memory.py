"""测试DM记忆功能 - 完整场景测试

验证DM能否记住之前提到的细节（如柜子里的物品）
"""

import sys
from pathlib import Path
import os
from dotenv import load_dotenv
import asyncio

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "web" / "backend"))

# 加载环境变量
load_dotenv(project_root / ".env")

from agents.dm_agent_langchain import DMAgentLangChain


async def test_dm_remembers_cabinet_items():
    """测试DM能否记住柜子里的物品（原始bug场景）"""

    print("=" * 80)
    print("🧪 DM记忆测试 - 柜子里的物品场景")
    print("=" * 80)

    dm_agent = DMAgentLangChain()

    game_state = {
        "version": "1.0.0",
        "turn_number": 0,
        "player": {
            "hp": 100,
            "maxHp": 100,
            "stamina": 100,
            "maxStamina": 100,
            "location": "神秘房间",
            "inventory": [],
            "level": 1
        },
        "world": {
            "time": 0,
            "theme": "奇幻世界",
            "current_location": "神秘房间"
        },
        "log": []
    }

    session_id = "memory_test"

    # ========== 第1回合：玩家扔金币到柜子里 ==========
    print("\n" + "━" * 80)
    print("📍 第1回合：玩家行动")
    print("━" * 80)
    print("玩家: 我把金币扔进柜子里的通风管道\n")

    print("DM回复:")
    print("-" * 80)

    full_response = []
    async for event in dm_agent.process_turn(
        session_id=session_id,
        player_action="我把金币扔进柜子里的通风管道",
        game_state=game_state
    ):
        if event["type"] == "narration":
            print(event["content"], end="", flush=True)
            full_response.append(event["content"])

    print("\n" + "-" * 80)

    dm_response_1 = "".join(full_response)

    # 检查DM是否提到了金币和柜子
    print("\n✅ 验证第1回合:")
    if "金币" in dm_response_1 or "coin" in dm_response_1.lower():
        print(f"  ✅ DM提到了金币")
    if "柜" in dm_response_1:
        print(f"  ✅ DM提到了柜子")

    print(f"\n📝 当前日志条目数: {len(game_state['log'])}")

    # ========== 第2回合：玩家往前走 ==========
    print("\n" + "━" * 80)
    print("📍 第2回合：玩家行动")
    print("━" * 80)
    print("玩家: 我往前走\n")

    print("DM回复:")
    print("-" * 80)

    full_response = []
    async for event in dm_agent.process_turn(
        session_id=session_id,
        player_action="我往前走",
        game_state=game_state
    ):
        if event["type"] == "narration":
            print(event["content"], end="", flush=True)
            full_response.append(event["content"])

    print("\n" + "-" * 80)

    dm_response_2 = "".join(full_response)

    print(f"\n📝 当前日志条目数: {len(game_state['log'])}")

    # ========== 第3回合：测试DM是否记得柜子里的金币 ==========
    print("\n" + "━" * 80)
    print("📍 第3回合：玩家行动（关键测试）")
    print("━" * 80)
    print("玩家: 刚才柜子里有什么来着？\n")

    print("DM回复:")
    print("-" * 80)

    full_response = []
    async for event in dm_agent.process_turn(
        session_id=session_id,
        player_action="刚才柜子里有什么来着？",
        game_state=game_state
    ):
        if event["type"] == "narration":
            print(event["content"], end="", flush=True)
            full_response.append(event["content"])

    print("\n" + "-" * 80)

    dm_response_3 = "".join(full_response)

    # ========== 验证DM记忆 ==========
    print("\n" + "=" * 80)
    print("🔍 DM记忆验证")
    print("=" * 80)

    remembered = False
    if "金币" in dm_response_3 or "coin" in dm_response_3.lower():
        print("✅ DM记得金币！")
        remembered = True
    else:
        print("❌ DM忘记了金币")

    if "通风管道" in dm_response_3 or "管道" in dm_response_3:
        print("✅ DM记得通风管道细节！")

    # 显示完整的对话历史
    print("\n📚 完整对话历史（game_state.log）:")
    print("-" * 80)
    for i, entry in enumerate(game_state['log']):
        actor = "🎮 玩家" if entry['actor'] == 'player' else "🎭 DM"
        text = entry['text'][:100] + "..." if len(entry['text']) > 100 else entry['text']
        print(f"{i+1}. {actor}: {text}")

    print("\n" + "=" * 80)
    if remembered:
        print("✅ 测试通过！DM成功记住了之前的对话内容")
    else:
        print("❌ 测试失败！DM未能记住之前的对话内容")
    print("=" * 80)

    return remembered


async def test_dm_remembers_npc_dialogue():
    """测试DM能否记住NPC说过的话"""

    print("\n\n" + "=" * 80)
    print("🧪 DM记忆测试 - NPC对话场景")
    print("=" * 80)

    dm_agent = DMAgentLangChain()

    game_state = {
        "version": "1.0.0",
        "turn_number": 0,
        "player": {
            "hp": 100,
            "maxHp": 100,
            "stamina": 100,
            "maxStamina": 100,
            "location": "酒馆",
            "inventory": [],
            "level": 1
        },
        "world": {
            "time": 0,
            "theme": "中世纪奇幻",
            "current_location": "酒馆"
        },
        "log": []
    }

    session_id = "npc_memory_test"

    # 第1回合：与老板娘对话
    print("\n" + "━" * 80)
    print("📍 第1回合")
    print("━" * 80)
    print("玩家: 我向酒馆老板娘打听关于失踪商人的消息\n")

    print("DM回复:")
    print("-" * 80)

    async for event in dm_agent.process_turn(
        session_id=session_id,
        player_action="我向酒馆老板娘打听关于失踪商人的消息",
        game_state=game_state
    ):
        if event["type"] == "narration":
            print(event["content"], end="", flush=True)

    print("\n" + "-" * 80)

    # 第2回合：玩家走开后又回来
    print("\n" + "━" * 80)
    print("📍 第2回合")
    print("━" * 80)
    print("玩家: 我走到窗边看了看，然后回到吧台\n")

    print("DM回复:")
    print("-" * 80)

    async for event in dm_agent.process_turn(
        session_id=session_id,
        player_action="我走到窗边看了看，然后回到吧台",
        game_state=game_state
    ):
        if event["type"] == "narration":
            print(event["content"], end="", flush=True)

    print("\n" + "-" * 80)

    # 第3回合：测试DM是否记得老板娘说过什么
    print("\n" + "━" * 80)
    print("📍 第3回合（关键测试）")
    print("━" * 80)
    print("玩家: 老板娘刚才说什么来着？\n")

    print("DM回复:")
    print("-" * 80)

    full_response = []
    async for event in dm_agent.process_turn(
        session_id=session_id,
        player_action="老板娘刚才说什么来着？",
        game_state=game_state
    ):
        if event["type"] == "narration":
            print(event["content"], end="", flush=True)
            full_response.append(event["content"])

    print("\n" + "-" * 80)

    dm_response = "".join(full_response)

    print("\n" + "=" * 80)
    print("🔍 验证结果")
    print("=" * 80)

    if "商人" in dm_response or "失踪" in dm_response:
        print("✅ DM成功回忆起老板娘关于失踪商人的对话")
        return True
    else:
        print("❌ DM未能回忆起之前的对话内容")
        return False


if __name__ == "__main__":
    print("\n🚀 开始DM记忆功能完整测试...\n")

    # 测试1: 柜子里的物品
    result1 = asyncio.run(test_dm_remembers_cabinet_items())

    # 测试2: NPC对话
    result2 = asyncio.run(test_dm_remembers_npc_dialogue())

    print("\n\n" + "=" * 80)
    print("📊 总测试结果")
    print("=" * 80)
    print(f"柜子物品记忆测试: {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"NPC对话记忆测试: {'✅ 通过' if result2 else '❌ 失败'}")
    print("=" * 80)

    if result1 and result2:
        print("\n🎉 所有测试通过！DM记忆功能正常工作")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试未通过")
        sys.exit(1)
