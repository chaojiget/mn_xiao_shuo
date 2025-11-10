"""简化的 LangGraph Checkpoint 测试

只测试核心功能：对话历史自动保存
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

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


async def main():
    """主测试函数"""

    checkpoint_db = "data/checkpoints/simple_test.db"
    Path(checkpoint_db).parent.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("🧪 LangGraph Checkpoint 简单测试")
    print("=" * 80)

    # 使用 async with 管理 checkpoint 连接
    async with AsyncSqliteSaver.from_conn_string(checkpoint_db) as checkpointer:

        # 创建模型
        model = ChatOpenAI(
            model="deepseek/deepseek-v3.1-terminus",
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=0.7
        )

        # 创建 Agent（带 checkpoint）
        agent = create_agent(
            model=model,
            tools=[],
            checkpointer=checkpointer  # 👈 关键
        )

        # 配置 thread_id
        thread_id = "test_001"
        config = {"configurable": {"thread_id": thread_id}}

        # 第1次对话
        print("\n[对话1]")
        print("玩家: 我叫张三，今年25岁")
        result1 = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "我叫张三，今年25岁"}]},
            config=config
        )
        print(f"Agent: {result1['messages'][-1].content}\n")

        # 第2次对话 - checkpoint 会自动加载历史
        print("[对话2]")
        print("玩家: 我叫什么名字？几岁？")
        result2 = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "我叫什么名字？几岁？"}]},
            config=config
        )
        print(f"Agent: {result2['messages'][-1].content}\n")

        # 验证
        response = result2['messages'][-1].content
        if "张三" in response and ("25" in response or "二十五" in response):
            print("✅ Checkpoint 成功！Agent 记住了之前的对话")
        else:
            print("❌ Checkpoint 失败！Agent 没有记住历史")

        # 查看 checkpoint 状态
        print("\n📊 Checkpoint 状态:")
        state = await checkpointer.aget(config)
        if state:
            print(f"  Thread ID: {thread_id}")
            if isinstance(state, dict) and 'messages' in state:
                print(f"  消息数量: {len(state['messages'])}")
                print(f"  ✅ Checkpoint 已持久化到: {checkpoint_db}")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
