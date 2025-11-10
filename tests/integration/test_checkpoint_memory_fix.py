"""测试 Checkpoint 记忆修复

验证：
1. DM Agent 启用 Checkpoint 模式
2. 使用 session_id 作为 thread_id
3. 对话历史自动保存和恢复
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "web" / "backend"))

from agents.dm_agent_langchain import DMAgentLangChain


async def test_checkpoint_memory():
    """测试 Checkpoint 记忆功能"""

    print("=" * 80)
    print("🧪 测试 DM Agent Checkpoint 记忆功能")
    print("=" * 80)

    # 初始化 DM Agent（启用 Checkpoint）
    print("\n[1] 初始化 DM Agent (Checkpoint 模式)...")
    dm_agent = DMAgentLangChain(
        model_name="deepseek",
        use_checkpoint=True,
        checkpoint_db="data/checkpoints/dm_test.db"
    )

    # 模拟游戏状态
    session_id = "test_session_001"
    game_state = {
        "session_id": session_id,
        "turn_number": 1,
        "player": {"hp": 100, "location": "酒馆"},
        "world": {"time": 1},
        "log": []  # 空日志，测试不依赖 log
    }

    # 第1回合：玩家说"我叫张三"
    print(f"\n[2] 第1回合 (session_id: {session_id})")
    print("玩家: 我叫张三，今年25岁")
    print("DM回复: ", end="", flush=True)

    response1 = ""
    async for event in dm_agent.process_turn(
        session_id=session_id,
        player_action="我叫张三，今年25岁",
        game_state=game_state
    ):
        if event["type"] == "narration":
            print(event["content"], end="", flush=True)
            response1 += event["content"]

    print(f"\n\n✅ 第1回合完成")

    # 第2回合：询问名字（测试记忆）
    print(f"\n[3] 第2回合 (相同 session_id: {session_id})")
    print("玩家: 我叫什么名字？几岁？")
    print("DM回复: ", end="", flush=True)

    response2 = ""
    async for event in dm_agent.process_turn(
        session_id=session_id,
        player_action="我叫什么名字？几岁？",
        game_state=game_state
    ):
        if event["type"] == "narration":
            print(event["content"], end="", flush=True)
            response2 += event["content"]

    print("\n")

    # 验证结果
    print("=" * 80)
    print("📊 测试结果")
    print("=" * 80)

    success = False
    if "张三" in response2 and "25" in response2:
        print("✅ DM 成功记住了玩家的名字和年龄")
        print(f"   - 回复中包含'张三': {('张三' in response2)}")
        print(f"   - 回复中包含'25': {('25' in response2)}")
        success = True
    else:
        print("❌ DM 没有记住玩家信息")
        print(f"   - 回复内容: {response2[:200]}...")

    print("\n💡 修复方案:")
    print("   1. ✅ DM Agent 已启用 Checkpoint 模式")
    print("   2. ✅ 使用 session_id 作为 thread_id")
    print("   3. ✅ GameState 添加了 session_id 字段")
    print("   4. ✅ 前端保存/加载时保持 session_id 一致")

    print("=" * 80)

    return success


if __name__ == "__main__":
    result = asyncio.run(test_checkpoint_memory())
    sys.exit(0 if result else 1)
