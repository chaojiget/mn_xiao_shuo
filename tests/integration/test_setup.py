#!/usr/bin/env python3
"""
快速测试脚本 - 验证项目设置
"""

import os
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)

    try:
        from src.models import (
            WorldState, Character, Location, Faction,
            EventNode, EventArc, ActionQueue, Clue, Setup, Evidence
        )
        print("✅ 数据模型导入成功")
    except Exception as e:
        print(f"❌ 数据模型导入失败: {e}")
        return False

    try:
        from src.llm import LiteLLMClient
        print("✅ LiteLLM 客户端导入成功")
    except Exception as e:
        print(f"❌ LiteLLM 客户端导入失败: {e}")
        return False

    return True


def test_data_models():
    """测试数据模型"""
    print("\n" + "=" * 60)
    print("测试 2: 数据模型创建")
    print("=" * 60)

    try:
        from src.models import WorldState, Character, EventNode, Clue

        # 创建世界状态
        world = WorldState(timestamp=0, turn=0)
        print("✅ WorldState 创建成功")

        # 创建角色
        protagonist = Character(
            id="CHAR-001",
            name="林墨",
            role="protagonist",
            attributes={"数据分析": 9},
            resources={"信用点": 50000}
        )
        world.characters["CHAR-001"] = protagonist
        print("✅ Character 创建成功")

        # 创建事件
        event = EventNode(
            id="EVENT-001",
            arc_id="ARC-1",
            title="发现异常",
            goal="收集初步证据",
            tension_delta=0.3
        )
        print("✅ EventNode 创建成功")

        # 创建线索
        clue = Clue(
            id="CLUE-001",
            content="产量数据异常",
            type="data_anomaly",
            evidence_ids=["EVIDENCE-001"]
        )
        print("✅ Clue 创建成功")

        return True

    except Exception as e:
        print(f"❌ 数据模型创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_files():
    """测试配置文件"""
    print("\n" + "=" * 60)
    print("测试 3: 配置文件")
    print("=" * 60)

    config_files = [
        "config/litellm_config.yaml",
        "config/novel_types.yaml",
        "examples/scifi_setting.json",
        "examples/xianxia_setting.json",
    ]

    all_ok = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file} 存在")
        else:
            print(f"❌ {config_file} 不存在")
            all_ok = False

    return all_ok


def test_env_file():
    """测试环境变量"""
    print("\n" + "=" * 60)
    print("测试 4: 环境变量")
    print("=" * 60)

    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env 文件不存在")
        print("   请执行: cp .env.example .env")
        print("   然后编辑 .env 填入你的 API keys")
        return False

    # 检查是否有 API key
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and api_key != "your_anthropic_api_key_here":
        print("✅ ANTHROPIC_API_KEY 已配置")
        return True
    else:
        print("⚠️  ANTHROPIC_API_KEY 未配置或使用默认值")
        print("   请在 .env 中填入你的 Anthropic API key")
        return False


def test_litellm_client():
    """测试 LiteLLM 客户端(仅配置加载)"""
    print("\n" + "=" * 60)
    print("测试 5: LiteLLM 客户端配置")
    print("=" * 60)

    try:
        from src.llm import LiteLLMClient

        client = LiteLLMClient()
        print("✅ LiteLLM 客户端初始化成功")

        models = client.list_models()
        print(f"✅ 可用模型: {', '.join(models)}")

        return True

    except FileNotFoundError as e:
        print(f"❌ 配置文件未找到: {e}")
        return False
    except Exception as e:
        print(f"❌ LiteLLM 客户端初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print(" 长篇小说生成系统 - 环境测试")
    print("=" * 60)

    results = {
        "模块导入": test_imports(),
        "数据模型": test_data_models(),
        "配置文件": test_config_files(),
        "环境变量": test_env_file(),
        "LiteLLM客户端": test_litellm_client(),
    }

    # 总结
    print("\n" + "=" * 60)
    print(" 测试总结")
    print("=" * 60)

    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过! 你可以开始开发了。")
        print("\n下一步:")
        print("1. 实现 src/director/gd.py (Global Director)")
        print("2. 参考 IMPLEMENTATION_GUIDE.md 的 Phase 1 任务")
    else:
        print("⚠️  部分测试失败,请检查上述错误信息。")
        print("\n常见问题:")
        print("- 如果缺少 .env 文件: cp .env.example .env")
        print("- 如果缺少依赖: pip install -r requirements.txt")

    print("=" * 60)


if __name__ == "__main__":
    main()
