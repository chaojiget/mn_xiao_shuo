"""测试带长期记忆的 DM Agent

演示如何使用 LangGraph Checkpoint + Store 实现：
1. 对话历史自动保存（Checkpoint）
2. 长期记忆管理（Store）
3. 跨会话记忆恢复
"""

import sys
from pathlib import Path
import asyncio
import os
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "web" / "backend"))

# 加载环境变量
load_dotenv(project_root / ".env")

from agents.dm_agent_with_memory import DMAgentWithMemory


async def scenario_1_first_encounter():
    """场景1: 首次遇到玩家"""

    print("=" * 80)
    print("🎮 场景1: 首次遇到玩家")
    print("=" * 80)

    async with DMAgentWithMemory() as dm:
        session_id = "game_session_001"
        user_id = "player_001"

        # 第1回合：玩家自我介绍
        print("\n[回合1] 玩家自我介绍")
        print("-" * 80)
        print("玩家: 你好，我叫李明，是一个喜欢探索的冒险者\n")
        print("DM回复:")

        async for event in dm.process_turn(
            session_id=session_id,
            player_action="你好，我叫李明，是一个喜欢探索的冒险者",
            user_id=user_id
        ):
            if event["type"] == "narration":
                print(event["content"], end="", flush=True)
            elif event["type"] == "tool_call":
                print(f"\n  [工具调用] {event['tool']}: {event['input']}")
            elif event["type"] == "tool_result":
                print(f"  [工具结果] {event['output']}")

        print("\n")

        # 第2回合：询问周围环境
        print("\n[回合2] 询问周围环境")
        print("-" * 80)
        print("玩家: 这里是什么地方？\n")
        print("DM回复:")

        async for event in dm.process_turn(
            session_id=session_id,
            player_action="这里是什么地方？",
            user_id=user_id
        ):
            if event["type"] == "narration":
                print(event["content"], end="", flush=True)

        print("\n")

        # 第3回合：重要事件
        print("\n[回合3] 遇到NPC")
        print("-" * 80)
        print("玩家: 我向酒馆老板娘打听关于失踪商人的消息\n")
        print("DM回复:")

        async for event in dm.process_turn(
            session_id=session_id,
            player_action="我向酒馆老板娘打听关于失踪商人的消息",
            user_id=user_id
        ):
            if event["type"] == "narration":
                print(event["content"], end="", flush=True)
            elif event["type"] == "tool_call":
                print(f"\n  [工具调用] {event['tool']}")

        print("\n")


async def scenario_2_continue_session():
    """场景2: 继续之前的会话"""

    print("\n\n" + "=" * 80)
    print("🎮 场景2: 继续之前的会话（测试对话历史恢复）")
    print("=" * 80)

    async with DMAgentWithMemory() as dm:
        session_id = "game_session_001"  # 相同的 session_id
        user_id = "player_001"

        # 询问之前的对话内容
        print("\n[回合4] 询问之前的对话")
        print("-" * 80)
        print("玩家: 老板娘刚才说了什么？\n")
        print("DM回复:")

        async for event in dm.process_turn(
            session_id=session_id,
            player_action="老板娘刚才说了什么？",
            user_id=user_id
        ):
            if event["type"] == "narration":
                print(event["content"], end="", flush=True)

        print("\n")


async def scenario_3_new_session_same_user():
    """场景3: 新会话，但同一个用户（测试长期记忆）"""

    print("\n\n" + "=" * 80)
    print("🎮 场景3: 新会话，同一个用户（测试长期记忆）")
    print("=" * 80)

    async with DMAgentWithMemory() as dm:
        session_id = "game_session_002"  # 不同的 session_id
        user_id = "player_001"  # 相同的 user_id

        # 询问玩家信息
        print("\n[新会话回合1] 询问玩家信息")
        print("-" * 80)
        print("玩家: 你还记得我吗？\n")
        print("DM回复:")

        async for event in dm.process_turn(
            session_id=session_id,
            player_action="你还记得我吗？",
            user_id=user_id
        ):
            if event["type"] == "narration":
                print(event["content"], end="", flush=True)
            elif event["type"] == "tool_call":
                print(f"\n  [工具调用] {event['tool']}")
            elif event["type"] == "tool_result":
                print(f"\n  [工具结果] {event['output']}")

        print("\n")


async def scenario_4_check_memory():
    """场景4: 查看保存的记忆"""

    print("\n\n" + "=" * 80)
    print("🎮 场景4: 查看保存的记忆")
    print("=" * 80)

    async with DMAgentWithMemory() as dm:
        session_id = "game_session_001"
        user_id = "player_001"

        # 回忆游戏记忆
        print("\n[测试] 回忆游戏记忆")
        print("-" * 80)
        print("玩家: 我之前有什么重要的经历？\n")
        print("DM回复:")

        async for event in dm.process_turn(
            session_id=session_id,
            player_action="我之前有什么重要的经历？",
            user_id=user_id
        ):
            if event["type"] == "narration":
                print(event["content"], end="", flush=True)
            elif event["type"] == "tool_call":
                print(f"\n  [工具调用] {event['tool']}")
            elif event["type"] == "tool_result":
                print(f"\n  [工具结果] {event['output']}")

        print("\n")


async def main():
    """主测试流程"""

    print("\n🚀 开始 DM Agent 长期记忆测试...\n")

    # 场景1: 首次遇到玩家
    await scenario_1_first_encounter()

    # 场景2: 继续之前的会话
    await scenario_2_continue_session()

    # 场景3: 新会话，同一个用户
    await scenario_3_new_session_same_user()

    # 场景4: 查看记忆
    await scenario_4_check_memory()

    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    print("✅ 对话历史自动保存（Checkpoint）")
    print("✅ 长期记忆管理（Store）")
    print("✅ 跨会话记忆恢复")
    print("\n💡 核心特性:")
    print("  1. 对话历史会自动保存到 Checkpoint")
    print("  2. 重要事件可以保存到 Store")
    print("  3. 新会话可以恢复玩家的长期记忆")
    print("  4. 无需手动管理消息历史")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
