#!/usr/bin/env python3
"""
测试 OpenRouter 集成
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()


async def test_openrouter():
    """测试 OpenRouter 集成"""
    from src.llm import LiteLLMClient

    print("=" * 60)
    print("测试 OpenRouter 集成")
    print("=" * 60)

    # 检查 API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key.startswith("your_"):
        print("❌ 请在 .env 文件中配置 OPENROUTER_API_KEY")
        return False

    print(f"✅ API Key 已配置 (前10位: {api_key[:10]}...)")

    try:
        # 创建客户端
        client = LiteLLMClient()
        print("✅ LiteLLM 客户端初始化成功")

        # 列出可用模型
        models = client.list_models()
        print(f"\n可用模型 ({len(models)} 个):")
        for model in models:
            print(f"  - {model}")

        # 测试各个模型
        test_prompts = {
            "claude-sonnet": "用一句话介绍科幻小说的魅力。",
            "deepseek": "用一句话介绍玄幻小说的特点。",
            "qwen": "用一句话说明什么是全局导演系统。",
        }

        print("\n" + "=" * 60)
        print("测试模型生成")
        print("=" * 60)

        for model_name, prompt in test_prompts.items():
            try:
                print(f"\n🔄 测试模型: {model_name}")
                print(f"提示: {prompt}")

                result = await client.generate(
                    prompt=prompt,
                    model=model_name,
                    max_tokens=150,
                    temperature=0.7
                )

                print(f"✅ 生成成功:")
                print(f"   {result}\n")

            except Exception as e:
                print(f"❌ 模型 {model_name} 测试失败: {e}\n")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_structured_output():
    """测试结构化输出"""
    from src.llm import LiteLLMClient

    print("\n" + "=" * 60)
    print("测试结构化输出 (JSON Schema)")
    print("=" * 60)

    client = LiteLLMClient()

    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "小说标题"},
            "genre": {"type": "string", "description": "类型(科幻/玄幻)"},
            "protagonist": {"type": "string", "description": "主角名字"},
            "setting": {"type": "string", "description": "背景设定,一句话"}
        },
        "required": ["title", "genre", "protagonist", "setting"]
    }

    prompt = "创建一个科幻小说的基本设定"

    try:
        result = await client.generate_structured(
            prompt=prompt,
            schema=schema,
            model="deepseek",  # 使用便宜的模型测试
            max_tokens=300
        )

        print("✅ 结构化输出成功:")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))

        return True

    except Exception as e:
        print(f"❌ 结构化输出测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_batch_generation():
    """测试批量生成"""
    from src.llm import LiteLLMClient

    print("\n" + "=" * 60)
    print("测试批量生成")
    print("=" * 60)

    client = LiteLLMClient()

    prompts = [
        "用10字描述科幻小说。",
        "用10字描述玄幻小说。",
        "用10字描述悬疑小说。",
    ]

    try:
        results = await client.batch_generate(
            prompts=prompts,
            model="qwen",  # 使用便宜快速的模型
            max_tokens=50
        )

        print("✅ 批量生成成功:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result}")

        return True

    except Exception as e:
        print(f"❌ 批量生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print(" OpenRouter + LiteLLM 集成测试")
    print("=" * 60)

    results = {
        "基础集成": await test_openrouter(),
        "结构化输出": await test_structured_output(),
        "批量生成": await test_batch_generation(),
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
        print("🎉 所有测试通过! OpenRouter 集成成功。")
        print("\n✨ 你现在可以:")
        print("1. 使用 Claude Sonnet 4.5 生成高质量内容")
        print("2. 使用 DeepSeek/Qwen 节省成本 (便宜10倍+)")
        print("3. 自动降级和重试机制")
        print("\n下一步: 开始实现 Global Director!")
    else:
        print("⚠️  部分测试失败,请检查:")
        print("1. .env 文件中的 OPENROUTER_API_KEY 是否正确")
        print("2. 网络连接是否正常")
        print("3. OpenRouter 账户是否有余额")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
