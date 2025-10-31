#!/usr/bin/env python3
"""测试聊天流式 API"""

import asyncio
import aiohttp
import json


async def test_chat_stream():
    """测试流式聊天接口"""

    url = "http://localhost:8000/api/chat/stream"

    # 测试数据
    payload = {
        "message": "生成一个科幻小说的开头，主角是一位星际飞行员",
        "novel_settings": {
            "title": "星际迷航",
            "type": "scifi",
            "protagonist": "年轻的星际飞行员，勇敢且充满好奇心",
            "background": "2350年，人类已经掌握了星际旅行技术"
        },
        "history": []
    }

    print("发送请求到:", url)
    print("请求数据:", json.dumps(payload, ensure_ascii=False, indent=2))
    print("\n" + "="*60)
    print("流式响应:")
    print("="*60 + "\n")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                print(f"错误: HTTP {response.status}")
                text = await response.text()
                print(text)
                return

            # 读取流式数据
            full_text = ""
            async for line in response.content:
                line_str = line.decode('utf-8').strip()

                if line_str.startswith("data: "):
                    try:
                        data = json.loads(line_str[6:])

                        if data.get("type") == "text":
                            content = data.get("content", "")
                            print(content, end="", flush=True)
                            full_text += content
                        elif data.get("type") == "done":
                            print("\n\n" + "="*60)
                            print("流式输出完成")
                            print("="*60)
                            break
                    except json.JSONDecodeError as e:
                        print(f"\n[解析错误: {e}]")

    print(f"\n总字数: {len(full_text)}")


async def test_with_history():
    """测试带历史记录的对话"""

    url = "http://localhost:8000/api/chat/stream"

    # 第一轮对话
    print("\n" + "="*60)
    print("第一轮对话: 生成开头")
    print("="*60 + "\n")

    payload1 = {
        "message": "生成一个简短的科幻故事开头",
        "novel_settings": {
            "title": "未来世界",
            "type": "scifi",
            "protagonist": "AI 研究员",
            "background": "2100年，AI 已经觉醒"
        },
        "history": []
    }

    first_response = ""
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload1) as response:
            async for line in response.content:
                line_str = line.decode('utf-8').strip()
                if line_str.startswith("data: "):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get("type") == "text":
                            content = data.get("content", "")
                            print(content, end="", flush=True)
                            first_response += content
                        elif data.get("type") == "done":
                            break
                    except:
                        pass

    # 第二轮对话（带历史记录）
    print("\n\n" + "="*60)
    print("第二轮对话: 继续剧情（基于上文）")
    print("="*60 + "\n")

    payload2 = {
        "message": "继续写下去，主角发现了什么？",
        "novel_settings": payload1["novel_settings"],
        "history": [
            {"role": "user", "content": "生成一个简短的科幻故事开头"},
            {"role": "assistant", "content": first_response}
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload2) as response:
            async for line in response.content:
                line_str = line.decode('utf-8').strip()
                if line_str.startswith("data: "):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get("type") == "text":
                            print(data.get("content", ""), end="", flush=True)
                        elif data.get("type") == "done":
                            break
                    except:
                        pass

    print("\n\n" + "="*60)
    print("对话测试完成")
    print("="*60)


if __name__ == "__main__":
    print("聊天流式 API 测试\n")

    # 测试基础流式输出
    print("测试 1: 基础流式输出")
    asyncio.run(test_chat_stream())

    print("\n\n")

    # 测试对话历史
    print("测试 2: 带历史记录的多轮对话")
    asyncio.run(test_with_history())
