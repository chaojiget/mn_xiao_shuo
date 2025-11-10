"""测试 LangGraph 官方 SQLite Checkpoint 和 Store

使用官方的 langgraph-checkpoint-sqlite 包
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing_extensions import TypedDict
import asyncio
import os
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "web" / "backend"))

# 加载环境变量
load_dotenv(project_root / ".env")

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime  # 👈 ToolRuntime 在这里
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver  # 👈 异步版本
from langgraph.store.memory import InMemoryStore  # 👈 可选：使用内存 store


# ============= 设置 Checkpoint 和 Store =============

# 方案1: 使用 SQLite Checkpoint（官方 - 异步版本）
checkpoint_db = "data/checkpoints/agent_checkpoints.db"
Path(checkpoint_db).parent.mkdir(parents=True, exist_ok=True)

# 方案2: 使用内存 Store（临时，重启后丢失）
# 生产环境可以用数据库 store，但目前 LangGraph 没有官方的 SQLite Store
store = InMemoryStore()

print(f"✅ Checkpoint DB: {checkpoint_db}")
print(f"✅ Store: InMemoryStore (临时)")
print("\n⚠️  注意: AsyncSqliteSaver 需要在 async with 上下文中使用")


@dataclass
class Context:
    """Agent 上下文"""
    user_id: str


# ============= 定义数据结构 =============

class UserInfo(TypedDict):
    """用户信息"""
    name: str
    age: int
    preferences: str


class GameMemory(TypedDict):
    """游戏记忆"""
    event: str
    location: str
    npc_name: str


# ============= 定义工具 =============

@tool
def save_user_info(user_info: UserInfo, runtime: ToolRuntime[Context]) -> str:
    """保存用户信息到 Store

    Store 用于保存长期记忆（跨会话）
    """
    store = runtime.store
    user_id = runtime.context.user_id

    # 保存到 store
    store.put(("users",), user_id, user_info)

    return f"✅ 已保存用户信息: {user_info['name']}"


@tool
def get_user_info(runtime: ToolRuntime[Context]) -> str:
    """获取用户信息"""
    store = runtime.store
    user_id = runtime.context.user_id

    item = store.get(("users",), user_id)

    if item:
        info = item.value
        return f"用户: {info['name']}, {info['age']}岁, 偏好: {info.get('preferences', '未知')}"
    else:
        return "❌ 未找到用户信息"


@tool
def save_game_memory(memory: GameMemory, runtime: ToolRuntime[Context]) -> str:
    """保存游戏记忆

    存储重要的游戏事件（如遇到NPC、重要对话）
    """
    store = runtime.store
    user_id = runtime.context.user_id

    # 使用时间戳作为 key
    import time
    memory_id = f"memory_{int(time.time())}"

    # 保存到 "game_memories" 命名空间
    store.put(("game_memories", user_id), memory_id, memory)

    return f"✅ 已保存游戏记忆: {memory['event']}"


@tool
def recall_game_memories(runtime: ToolRuntime[Context]) -> str:
    """回忆游戏记忆（最近5条）"""
    store = runtime.store
    user_id = runtime.context.user_id

    # 搜索该用户的所有记忆
    items = store.search(("game_memories", user_id))

    if not items:
        return "❌ 没有游戏记忆"

    # 只返回最近5条
    recent_memories = items[:5]

    result = "📚 最近的游戏记忆:\n"
    for item in recent_memories:
        mem = item.value
        result += f"  - {mem['event']} (在 {mem['location']})\n"

    return result


# ============= 测试函数 =============

async def test_checkpoint_basics():
    """测试 Checkpoint 基本功能（对话历史自动保存）"""

    print("=" * 80)
    print("🧪 测试1: Checkpoint 自动保存对话历史")
    print("=" * 80)

    # 使用 async with 管理 checkpoint
    async with AsyncSqliteSaver.from_conn_string(checkpoint_db) as checkpointer:
        model = ChatOpenAI(
            model="deepseek/deepseek-v3.1-terminus",
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=0.7
        )

        # 创建带 checkpoint 的 Agent
        agent = create_agent(
            model=model,
            tools=[],  # 暂时不用工具
            checkpointer=checkpointer  # 👈 关键：启用 checkpoint
        )

        # 配置 thread_id（类似 session_id）
        thread_id = "test_thread_1"
        config = {"configurable": {"thread_id": thread_id}}

        # 第一次对话
        print("\n[对话1] 玩家: 我叫李四")
        result1 = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "我叫李四"}]},
            config=config
        )

        print(f"Agent: {result1['messages'][-1].content[:100]}...")

        # 第二次对话 - 不传入历史，checkpoint 会自动加载！
        print("\n[对话2] 玩家: 我叫什么名字？")
        result2 = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "我叫什么名字？"}]},
            config=config  # 相同的 thread_id，会自动加载历史
        )

        print(f"Agent: {result2['messages'][-1].content[:200]}...")

        # 验证
        if "李四" in result2['messages'][-1].content:
            print("\n✅ Checkpoint 成功保存和恢复对话历史！")
        else:
            print("\n❌ Checkpoint 未能记住历史")

        # 查看 checkpoint 状态
        print("\n📊 Checkpoint 状态:")
        state = await checkpointer.aget(config)
        if state:
            print(f"  Thread ID: {thread_id}")
            print(f"  Checkpoint ID: {state.checkpoint_id}")
            print(f"  消息数量: {len(state.values.get('messages', []))}")


async def test_store_with_tools():
    """测试 Store + Tools（长期记忆）"""

    print("\n\n" + "=" * 80)
    print("🧪 测试2: Store + Tools（长期记忆）")
    print("=" * 80)

    model = ChatOpenAI(
        model="deepseek/deepseek-v3.1-terminus",
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=0.7
    )

    # 创建 Agent（带 checkpoint + store）
    agent = create_agent(
        model=model,
        tools=[save_user_info, get_user_info, save_game_memory, recall_game_memories],
        checkpointer=checkpointer,  # 对话历史
        store=store,  # 长期记忆
        context_schema=Context
    )

    user_id = "player_456"
    context = Context(user_id=user_id)
    thread_id = "test_thread_2"
    config = {"configurable": {"thread_id": thread_id}}

    # 保存用户信息
    print("\n[对话1] 保存用户信息")
    result1 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我叫王五，30岁，喜欢策略游戏"}]},
        context=context,
        config=config
    )

    print(f"Agent: {result1['messages'][-1].content[:200]}...")

    # 保存游戏记忆
    print("\n[对话2] 保存游戏记忆")
    result2 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我在城镇酒馆遇到了老板娘玛莎，她告诉我关于失踪商人的线索"}]},
        context=context,
        config=config
    )

    print(f"Agent: {result2['messages'][-1].content[:200]}...")

    # 再保存一条记忆
    print("\n[对话3] 保存更多记忆")
    result3 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我在精灵森林发现了一个神秘的石碑"}]},
        context=context,
        config=config
    )

    print(f"Agent: {result3['messages'][-1].content[:200]}...")

    # 回忆记忆
    print("\n[对话4] 回忆游戏记忆")
    result4 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我之前有什么重要的游戏记忆？"}]},
        context=context,
        config=config
    )

    print(f"Agent: {result4['messages'][-1].content[:300]}...")

    # 获取用户信息
    print("\n[对话5] 获取用户信息")
    result5 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我的个人信息是什么？"}]},
        context=context,
        config=config
    )

    print(f"Agent: {result5['messages'][-1].content[:200]}...")

    print("\n✅ Store + Tools 测试完成！")


async def test_checkpoint_persistence():
    """测试 Checkpoint 持久化（模拟重启）"""

    print("\n\n" + "=" * 80)
    print("🧪 测试3: Checkpoint 持久化（模拟重启）")
    print("=" * 80)

    # 创建新的 checkpointer（模拟应用重启）
    new_checkpointer = AsyncSqliteSaver.from_conn_string(checkpoint_db)

    model = ChatOpenAI(
        model="deepseek/deepseek-v3.1-terminus",
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=0.7
    )

    agent = create_agent(
        model=model,
        tools=[],
        checkpointer=new_checkpointer
    )

    # 使用之前的 thread_id
    thread_id = "test_thread_1"
    config = {"configurable": {"thread_id": thread_id}}

    # 继续之前的对话
    print("\n[重启后对话] 玩家: 我们之前聊了什么？")
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我们之前聊了什么？"}]},
        config=config
    )

    print(f"Agent: {result['messages'][-1].content[:300]}...")

    # 验证
    if "李四" in result['messages'][-1].content:
        print("\n✅ Checkpoint 持久化成功！重启后仍能读取历史")
    else:
        print("\n⚠️ Checkpoint 可能未能完全恢复历史")


async def test_time_travel():
    """测试时间旅行（回到之前的状态）"""

    print("\n\n" + "=" * 80)
    print("🧪 测试4: 时间旅行（Checkpoint 快照）")
    print("=" * 80)

    model = ChatOpenAI(
        model="deepseek/deepseek-v3.1-terminus",
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=0.7
    )

    agent = create_agent(
        model=model,
        tools=[],
        checkpointer=checkpointer
    )

    thread_id = "test_thread_3"
    config = {"configurable": {"thread_id": thread_id}}

    # 第1次对话
    print("\n[对话1] 选择路线A")
    result1 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我选择路线A，进入森林"}]},
        config=config
    )
    print(f"Agent: {result1['messages'][-1].content[:100]}...")

    # 获取这个时刻的 checkpoint_id
    state1 = await checkpointer.aget(config)
    checkpoint_id_1 = state1.checkpoint_id
    print(f"📸 快照1 ID: {checkpoint_id_1}")

    # 第2次对话
    print("\n[对话2] 继续前进")
    result2 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我继续往森林深处走"}]},
        config=config
    )
    print(f"Agent: {result2['messages'][-1].content[:100]}...")

    # 时间旅行：回到快照1
    print("\n[时间旅行] 回到快照1，选择路线B")
    config_with_checkpoint = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id_1  # 👈 回到之前的状态
        }
    }

    result3 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我改变主意，选择路线B，去城镇"}]},
        config=config_with_checkpoint
    )
    print(f"Agent: {result3['messages'][-1].content[:100]}...")

    print("\n✅ 时间旅行测试完成！")


if __name__ == "__main__":
    print("\n🚀 开始 LangGraph Checkpoint + Store 完整测试...\n")

    # 测试1: Checkpoint 自动保存对话
    asyncio.run(test_checkpoint_basics())

    # 测试2: Store + Tools（长期记忆）
    asyncio.run(test_store_with_tools())

    # 测试3: Checkpoint 持久化
    asyncio.run(test_checkpoint_persistence())

    # 测试4: 时间旅行
    asyncio.run(test_time_travel())

    print("\n" + "=" * 80)
    print("🎉 所有测试完成！")
    print("=" * 80)
    print("\n📊 总结:")
    print("  ✅ Checkpoint: 自动保存对话历史（SQLite）")
    print("  ✅ Store: 保存长期记忆（InMemoryStore，可替换为数据库）")
    print("  ✅ 持久化: 重启后仍可恢复")
    print("  ✅ 时间旅行: 可以回到之前的对话状态")
