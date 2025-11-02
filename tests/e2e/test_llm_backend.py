#!/usr/bin/env python3
"""测试 LLM 后端"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from web.backend.llm import create_backend
from web.backend.llm.config_loader import LLMConfigLoader
from web.backend.llm.base import LLMMessage

async def test_llm():
    """测试 LLM 后端流式生成"""
    print("1. 加载配置...")
    config_loader = LLMConfigLoader()
    backend_type = config_loader.get_backend_type()
    backend_config = config_loader.get_backend_config()

    print(f"   后端类型: {backend_type}")
    print(f"   后端配置: {backend_config}")

    print("\n2. 创建后端...")
    llm_backend = create_backend(backend_type, backend_config)
    print(f"   后端创建成功: {llm_backend}")

    print("\n3. 测试流式生成...")
    messages = [
        LLMMessage(role="system", content="你是一个有用的助手"),
        LLMMessage(role="user", content="你好，请说一句话")
    ]

    print("   开始生成...")
    full_response = ""
    try:
        async for chunk in llm_backend.generate_stream(
            messages=messages,
            temperature=0.7,
            max_tokens=100
        ):
            print(f"   收到chunk: {chunk[:50]}...")
            full_response += chunk
    except Exception as e:
        print(f"   ❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print(f"\n4. 完整响应:\n{full_response}")
    print("\n✅ 测试成功!")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_llm())
    sys.exit(0 if result else 1)
