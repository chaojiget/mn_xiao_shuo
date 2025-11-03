"""
Claude Agent SDK 集成测试
测试 @tool + MCP Server + DM Agent
"""

import pytest
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "web" / "backend"))

try:
    from claude_agent_sdk import tool, create_sdk_mcp_server
    from agents.game_tools_mcp import ALL_GAME_TOOLS, init_state_manager
    from agents.mcp_servers import create_game_mcp_server
    from agents.dm_agent import DMAgent
    CLAUDE_SDK_AVAILABLE = True
except ImportError as e:
    CLAUDE_SDK_AVAILABLE = False
    print(f"⚠️  Claude Agent SDK 不可用: {e}")


pytestmark = pytest.mark.skipif(
    not CLAUDE_SDK_AVAILABLE,
    reason="需要 Claude Agent SDK"
)


def test_import_claude_sdk():
    """测试 Claude Agent SDK 导入"""
    assert CLAUDE_SDK_AVAILABLE
    assert tool is not None
    assert create_sdk_mcp_server is not None
    print("✅ Claude Agent SDK 导入成功")


def test_tools_defined():
    """测试工具定义"""
    assert len(ALL_GAME_TOOLS) > 0
    print(f"✅ 工具数量: {len(ALL_GAME_TOOLS)}")

    # 验证工具是 SdkMcpTool 对象
    for tool_obj in ALL_GAME_TOOLS:
        assert hasattr(tool_obj, 'name')
        assert hasattr(tool_obj, 'description')
        assert hasattr(tool_obj, 'handler')
        print(f"   - {tool_obj.name}: {tool_obj.description}")


def test_create_mcp_server():
    """测试创建 MCP Server"""
    # 初始化状态管理器（使用 None 作为 db）
    init_state_manager(None)

    # 创建 MCP Server
    server = create_game_mcp_server(None)

    assert server is not None
    print(f"✅ MCP Server 创建成功: {server}")


def test_dm_agent_initialization():
    """测试 DM Agent 初始化"""
    # 初始化状态管理器
    init_state_manager(None)

    # 创建 DM Agent
    dm_agent = DMAgent()

    assert dm_agent is not None
    assert dm_agent.game_server is not None
    assert dm_agent.base_options is not None
    print("✅ DM Agent 初始化成功")


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要 API Key，手动运行")
async def test_dm_agent_process_turn():
    """测试 DM Agent 处理回合"""
    # 初始化
    init_state_manager(None)
    dm_agent = DMAgent()

    # 测试状态
    game_state = {
        "player": {
            "hp": 100,
            "max_hp": 100,
            "inventory": [],
            "gold": 10
        },
        "world": {
            "current_location": "起始村庄",
            "theme": "奇幻世界"
        },
        "turn_number": 0
    }

    # 处理回合
    result = await dm_agent.process_turn_sync(
        session_id="test_001",
        player_action="我环顾四周",
        game_state=game_state
    )

    assert "narration" in result
    assert result["turn"] == 1
    print(f"✅ 回合处理成功")
    print(f"旁白: {result['narration'][:100]}...")


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要 API Key，手动运行")
async def test_dm_agent_with_tools():
    """测试 DM Agent 工具调用"""
    init_state_manager(None)
    dm_agent = DMAgent()

    game_state = {
        "player": {"hp": 100, "max_hp": 100, "inventory": [], "gold": 10},
        "world": {"current_location": "起始村庄", "theme": "奇幻世界"},
        "turn_number": 0
    }

    # 测试工具调用
    result = await dm_agent.process_turn_sync(
        session_id="test_002",
        player_action="我拾起地上的铁剑",
        game_state=game_state
    )

    # 验证工具被调用
    assert len(result["tool_calls"]) > 0
    print(f"✅ 工具调用测试成功")
    print(f"工具调用: {result['tool_calls']}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
