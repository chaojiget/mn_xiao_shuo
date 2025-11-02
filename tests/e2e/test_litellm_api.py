#!/usr/bin/env python3
"""
测试 LiteLLM Proxy API
"""
import asyncio
import httpx
import json
import os


async def test_deepseek():
    """测试 DeepSeek 模型"""
    print("测试 DeepSeek 模型...")

    # 从环境变量读取 master key
    master_key = os.environ.get("LITELLM_MASTER_KEY", "sk-123")
    print(f"使用 Master Key: {master_key}")

    async with httpx.AsyncClient(
        base_url="http://localhost:4000",
        headers={"Authorization": f"Bearer {master_key}"},
        timeout=60.0
    ) as client:
        # 测试普通调用
        response = await client.post(
            "/chat/completions",
            json={
                "model": "deepseek",
                "messages": [
                    {"role": "user", "content": "你好，请用一句话介绍一下你自己"}
                ],
                "temperature": 0.7,
                "max_tokens": 100
            }
        )

        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

        if "choices" in result:
            print(f"\n生成内容: {result['choices'][0]['message']['content']}")


async def test_streaming():
    """测试流式输出"""
    print("\n\n测试流式输出...")

    # 从环境变量读取 master key
    master_key = os.environ.get("LITELLM_MASTER_KEY", "sk-123")

    async with httpx.AsyncClient(
        base_url="http://localhost:4000",
        headers={"Authorization": f"Bearer {master_key}"},
        timeout=60.0
    ) as client:
        async with client.stream(
            "POST",
            "/chat/completions",
            json={
                "model": "deepseek",
                "messages": [
                    {"role": "user", "content": "请写一首关于春天的短诗"}
                ],
                "temperature": 0.7,
                "max_tokens": 200,
                "stream": True
            }
        ) as response:
            print(f"状态码: {response.status_code}")
            print("流式输出:")

            full_content = ""
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                print(content, end="", flush=True)
                                full_content += content
                    except json.JSONDecodeError:
                        continue

            print(f"\n\n完整内容: {full_content}")


async def main():
    try:
        await test_deepseek()
        await test_streaming()
        print("\n✅ 测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
