"""
测试 LangChain 迁移
验证新的 LangChain 架构是否正常工作
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_import_game_tools():
    """测试游戏工具导入"""
    try:
        from web.backend.agents.game_tools_langchain import (
            get_player_state,
            add_item,
            update_hp,
            roll_check,
            set_location,
            save_game,
            ALL_GAME_TOOLS
        )
        assert len(ALL_GAME_TOOLS) == 15, f"应该有15个工具，实际有{len(ALL_GAME_TOOLS)}个"
        print("✅ 游戏工具导入成功")
        return True
    except ImportError as e:
        pytest.fail(f"导入游戏工具失败: {e}")


def test_import_dm_agent():
    """测试 DM Agent 导入"""
    try:
        from web.backend.agents.dm_agent_langchain import DMAgentLangChain
        print("✅ DM Agent 导入成功")
        return True
    except ImportError as e:
        pytest.fail(f"导入 DM Agent 失败: {e}")


def test_import_langchain_backend():
    """测试 LangChain 后端导入"""
    try:
        from web.backend.llm.langchain_backend import LangChainBackend
        from web.backend.llm import create_backend, get_available_backends

        backends = get_available_backends()
        assert "langchain" in backends, "应该有 langchain 后端"
        assert backends["langchain"]["available"] is True

        print("✅ LangChain 后端导入成功")
        return True
    except ImportError as e:
        pytest.fail(f"导入 LangChain 后端失败: {e}")


def test_state_manager():
    """测试状态管理器"""
    try:
        from web.backend.agents.game_tools_langchain import (
            state_manager,
            set_current_session_id,
            get_current_session_id
        )

        # 测试会话ID管理
        test_session = "test_session_123"
        set_current_session_id(test_session)
        assert get_current_session_id() == test_session

        # 测试状态获取
        state = state_manager.get_state(test_session)
        assert "player" in state
        assert "world" in state
        assert state["player"]["hp"] == 100

        print("✅ 状态管理器工作正常")
        return True
    except Exception as e:
        pytest.fail(f"状态管理器测试失败: {e}")


def test_tool_definitions():
    """测试工具定义"""
    try:
        from web.backend.agents.game_tools_langchain import ALL_GAME_TOOLS

        # 检查每个工具都有必要的属性
        for tool in ALL_GAME_TOOLS:
            assert hasattr(tool, "name"), f"工具 {tool} 缺少 name 属性"
            assert hasattr(tool, "description"), f"工具 {tool} 缺少 description 属性"
            assert callable(tool.func), f"工具 {tool} 不可调用"

        print(f"✅ 所有 {len(ALL_GAME_TOOLS)} 个工具定义正确")
        return True
    except Exception as e:
        pytest.fail(f"工具定义测试失败: {e}")


@pytest.mark.asyncio
async def test_langchain_backend_init():
    """测试 LangChain 后端初始化"""
    try:
        from web.backend.llm.langchain_backend import LangChainBackend

        # 测试初始化（不需要真实 API Key）
        config = {
            "model": "deepseek",
            "temperature": 0.7
        }

        # 注意: 这里不设置 OPENROUTER_API_KEY，只测试初始化
        import os
        os.environ["OPENROUTER_API_KEY"] = "test-key"

        backend = LangChainBackend(config)

        assert backend.model is not None
        assert backend.get_model_name() is not None

        info = backend.get_backend_info()
        assert info["backend"] == "LangChain"

        print("✅ LangChain 后端初始化成功")
        return True
    except Exception as e:
        pytest.fail(f"后端初始化测试失败: {e}")


def test_no_old_dependencies():
    """测试旧依赖已移除"""
    import subprocess

    # 检查 requirements.txt
    req_file = project_root / "requirements.txt"
    content = req_file.read_text()

    # 应该不包含这些旧依赖
    assert "litellm" not in content.lower(), "requirements.txt 仍包含 litellm"
    assert "anthropic" not in content.lower(), "requirements.txt 仍包含 anthropic"

    # 应该包含这些新依赖
    assert "langchain" in content.lower(), "requirements.txt 缺少 langchain"

    print("✅ 依赖检查通过")
    return True


def test_env_example_updated():
    """测试 .env.example 已更新"""
    env_file = project_root / ".env.example"
    content = env_file.read_text()

    # 应该不包含旧配置
    assert "LITELLM" not in content, ".env.example 仍包含 LITELLM 配置"
    assert "ANTHROPIC_BASE_URL" not in content, ".env.example 仍包含 ANTHROPIC_BASE_URL"

    # 应该包含新配置
    assert "OPENROUTER_BASE_URL" in content, ".env.example 缺少 OPENROUTER_BASE_URL"
    assert "DEFAULT_MODEL" in content, ".env.example 缺少 DEFAULT_MODEL"

    print("✅ .env.example 已正确更新")
    return True


if __name__ == "__main__":
    """直接运行此文件进行快速测试"""
    print("=" * 50)
    print("LangChain 迁移测试")
    print("=" * 50)

    tests = [
        ("导入游戏工具", test_import_game_tools),
        ("导入 DM Agent", test_import_dm_agent),
        ("导入 LangChain 后端", test_import_langchain_backend),
        ("状态管理器", test_state_manager),
        ("工具定义", test_tool_definitions),
        ("依赖检查", test_no_old_dependencies),
        ("环境配置", test_env_example_updated),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            print(f"\n测试: {name}...")
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ 失败: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 50)

    if failed == 0:
        print("\n🎉 所有测试通过！LangChain 迁移成功！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查")
        sys.exit(1)
