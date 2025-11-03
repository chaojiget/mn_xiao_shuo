"""
MCP Server 创建 - 使用 Claude Agent SDK
基于 docs/TECHNICAL_IMPLEMENTATION_PLAN.md 第4.2节设计
"""

from claude_agent_sdk import create_sdk_mcp_server
from .game_tools_mcp import ALL_GAME_TOOLS, init_state_manager


def create_game_mcp_server(db_connection):
    """创建游戏工具 MCP Server

    Args:
        db_connection: 数据库连接对象

    Returns:
        MCP Server 实例
    """
    # 初始化状态管理器
    init_state_manager(db_connection)

    # 创建 MCP Server
    server = create_sdk_mcp_server(
        name="game-tools",
        version="1.0.0",
        tools=ALL_GAME_TOOLS
    )

    return server


# 使用示例
def get_game_server():
    """获取游戏 MCP Server（单例）"""
    try:
        from ..database.world_db import WorldDatabase
        # 获取数据库连接
        db = WorldDatabase("data/sqlite/game.db")
    except:
        db = None

    # 创建 MCP Server
    return create_game_mcp_server(db)
