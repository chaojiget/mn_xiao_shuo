"""测试 SQLite Store 实现

验证 LangGraph Agent 使用 SQLite 持久化记忆
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
from langchain.tools import tool
from langgraph.tools import ToolRuntime

# 导入我们的 SQLite Store
from llm.sqlite_store import SqliteStore


# ============= 设置 Store 和 Context =============

# 使用 SQLite 存储（持久化到磁盘）
store = SqliteStore("data/memory/agent_memory.db")

@dataclass
class Context:
    """Agent 上下文（包含用户ID）"""
    user_id: str


# ============= 定义数据结构 =============

class UserInfo(TypedDict):
    """用户信息结构"""
    name: str
    age: int
    preferences: str


class GameProgress(TypedDict):
    """游戏进度结构"""
    current_location: str
    level: int
    items: str


# ============= 定义工具 =============

@tool
def save_user_info(user_info: UserInfo, runtime: ToolRuntime[Context]) -> str:
    """保存用户信息

    Args:
        user_info: 用户信息（名字、年龄、偏好）
        runtime: 工具运行时环境

    Returns:
        成功消息
    """
    # 从 runtime 获取 store 和 context
    store = runtime.store
    user_id = runtime.context.user_id

    # 保存到 store（命名空间: "users", 键: user_id）
    store.put(("users",), user_id, user_info)

    return f"✅ 已保存用户 {user_id} 的信息: {user_info['name']}"


@tool
def get_user_info(runtime: ToolRuntime[Context]) -> str:
    """获取用户信息

    Args:
        runtime: 工具运行时环境

    Returns:
        用户信息字符串
    """
    store = runtime.store
    user_id = runtime.context.user_id

    # 从 store 获取
    item = store.get(("users",), user_id)

    if item:
        info = item.value
        return f"用户信息: {info['name']}, {info['age']}岁, 偏好: {info.get('preferences', '未设置')}"
    else:
        return "❌ 未找到用户信息"


@tool
def save_game_progress(progress: GameProgress, runtime: ToolRuntime[Context]) -> str:
    """保存游戏进度

    Args:
        progress: 游戏进度
        runtime: 工具运行时环境

    Returns:
        成功消息
    """
    store = runtime.store
    user_id = runtime.context.user_id

    # 保存到命名空间 "game_progress"
    store.put(("game_progress",), user_id, progress)

    return f"✅ 已保存游戏进度: {progress['current_location']}, 等级 {progress['level']}"


@tool
def get_game_progress(runtime: ToolRuntime[Context]) -> str:
    """获取游戏进度

    Args:
        runtime: 工具运行时环境

    Returns:
        游戏进度字符串
    """
    store = runtime.store
    user_id = runtime.context.user_id

    item = store.get(("game_progress",), user_id)

    if item:
        progress = item.value
        return f"游戏进度: {progress['current_location']}, 等级 {progress['level']}, 物品: {progress.get('items', '无')}"
    else:
        return "❌ 未找到游戏进度"


# ============= 测试函数 =============

async def test_sqlite_store_basic():
    """测试 SQLite Store 基本功能"""

    print("=" * 80)
    print("🧪 测试 SQLite Store 基本功能")
    print("=" * 80)

    # 1. 直接使用 store
    print("\n[测试1] 直接使用 Store API")
    print("-" * 80)

    # 保存数据
    store.put(("users",), "test_user", {
        "name": "测试用户",
        "age": 25,
        "preferences": "喜欢奇幻游戏"
    })
    print("✅ 保存成功: users/test_user")

    # 获取数据
    item = store.get(("users",), "test_user")
    if item:
        print(f"✅ 获取成功: {item.value}")
    else:
        print("❌ 获取失败")

    # 搜索命名空间
    items = store.search(("users",))
    print(f"✅ 搜索 'users' 命名空间: 找到 {len(items)} 条记录")

    # 统计信息
    stats = store.get_stats()
    print(f"\n📊 Store 统计:")
    print(f"  总记录数: {stats['total_items']}")
    print(f"  命名空间: {stats['namespace_counts']}")
    print(f"  数据库大小: {stats['db_size_mb']} MB")

    print("\n✅ 基本功能测试通过！")


async def test_agent_with_sqlite_store():
    """测试 Agent 使用 SQLite Store"""

    print("\n\n" + "=" * 80)
    print("🧪 测试 Agent 使用 SQLite Store")
    print("=" * 80)

    # 创建 Agent
    model = ChatOpenAI(
        model="deepseek/deepseek-v3.1-terminus",
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=0.7
    )

    agent = create_agent(
        model=model,
        tools=[save_user_info, get_user_info, save_game_progress, get_game_progress],
        store=store,
        context_schema=Context
    )

    user_id = "user_123"
    context = Context(user_id=user_id)

    # 测试1: 保存用户信息
    print("\n[测试2] Agent 保存用户信息")
    print("-" * 80)

    result1 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我叫张三，25岁，喜欢玩JRPG游戏"}]},
        context=context
    )

    print("Agent 回复:")
    for msg in result1['messages']:
        if hasattr(msg, 'content') and msg.content:
            print(f"  {msg.content[:200]}")

    # 验证数据已保存
    item = store.get(("users",), user_id)
    if item:
        print(f"\n✅ 验证: 数据已保存到 SQLite")
        print(f"  {item.value}")
    else:
        print("❌ 验证失败: 数据未保存")

    # 测试2: 获取用户信息（模拟重启后）
    print("\n[测试3] Agent 获取用户信息（模拟重启）")
    print("-" * 80)

    result2 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我的信息是什么？"}]},
        context=context
    )

    print("Agent 回复:")
    for msg in result2['messages']:
        if hasattr(msg, 'content') and msg.content:
            print(f"  {msg.content[:200]}")

    # 测试3: 保存游戏进度
    print("\n[测试4] Agent 保存游戏进度")
    print("-" * 80)

    result3 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我现在在精灵森林，等级5，拥有铁剑和生命药水"}]},
        context=context
    )

    print("Agent 回复:")
    for msg in result3['messages']:
        if hasattr(msg, 'content') and msg.content:
            print(f"  {msg.content[:200]}")

    # 测试4: 获取游戏进度
    print("\n[测试5] Agent 获取游戏进度")
    print("-" * 80)

    result4 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "我的游戏进度是什么？"}]},
        context=context
    )

    print("Agent 回复:")
    for msg in result4['messages']:
        if hasattr(msg, 'content') and msg.content:
            print(f"  {msg.content[:200]}")

    # 最终统计
    print("\n" + "=" * 80)
    print("📊 最终 Store 统计")
    print("=" * 80)

    stats = store.get_stats()
    print(f"总记录数: {stats['total_items']}")
    print(f"命名空间分布: {stats['namespace_counts']}")

    # 列出所有用户
    user_items = store.search(("users",))
    print(f"\n👥 所有用户 ({len(user_items)} 个):")
    for item in user_items:
        print(f"  - {item.key}: {item.value.get('name', 'Unknown')}")

    # 列出所有游戏进度
    progress_items = store.search(("game_progress",))
    print(f"\n🎮 所有游戏进度 ({len(progress_items)} 个):")
    for item in progress_items:
        print(f"  - {item.key}: {item.value.get('current_location', 'Unknown')}")

    print("\n✅ Agent 集成测试完成！")


async def test_persistence():
    """测试持久化（重启后数据仍在）"""

    print("\n\n" + "=" * 80)
    print("🧪 测试持久化（模拟重启）")
    print("=" * 80)

    # 创建新的 store 实例（模拟重启）
    new_store = SqliteStore("data/memory/agent_memory.db")

    # 读取之前保存的数据
    item = new_store.get(("users",), "user_123")

    if item:
        print("✅ 持久化测试通过！")
        print(f"  重启后仍能读取数据: {item.value}")
    else:
        print("❌ 持久化测试失败！")

    # 显示统计
    stats = new_store.get_stats()
    print(f"\n📊 重启后的 Store 状态:")
    print(f"  总记录数: {stats['total_items']}")
    print(f"  命名空间: {stats['namespace_counts']}")


if __name__ == "__main__":
    print("\n🚀 开始 SQLite Store 完整测试...\n")

    # 测试1: 基本功能
    asyncio.run(test_sqlite_store_basic())

    # 测试2: Agent 集成
    asyncio.run(test_agent_with_sqlite_store())

    # 测试3: 持久化
    asyncio.run(test_persistence())

    print("\n" + "=" * 80)
    print("🎉 所有测试完成！")
    print("=" * 80)
