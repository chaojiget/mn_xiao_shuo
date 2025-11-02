"""聊天 API - 流式响应"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncGenerator, Optional, List, Dict, Any
import json
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm import create_backend
from llm.config_loader import LLMConfigLoader
from llm.base import LLMMessage

router = APIRouter()

# 全局 LLM 后端
llm_backend = None


class NovelSettings(BaseModel):
    """小说设定"""
    id: Optional[str] = None
    title: str = ""
    type: str = "scifi"
    protagonist: str = ""
    background: str = ""
    characters: List[str] = []


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    conversation_id: Optional[str] = None
    novel_settings: Optional[NovelSettings] = None
    history: List[Dict[str, Any]] = []  # 对话历史 [{"role": "user/assistant", "content": "..."}]


async def generate_stream_response(
    message: str,
    novel_settings: Optional[NovelSettings] = None,
    history: Optional[List[Dict[str, Any]]] = None
) -> AsyncGenerator[str, None]:
    """
    生成流式响应 - 使用 LLM 后端抽象层

    Args:
        message: 用户消息
        novel_settings: 小说设定
        history: 对话历史
    """
    global llm_backend

    # 初始化 LLM 后端
    if llm_backend is None:
        config_loader = LLMConfigLoader()
        backend_type = config_loader.get_backend_type()
        backend_config = config_loader.get_backend_config()
        llm_backend = create_backend(backend_type, backend_config)

    try:
        # 构建系统提示词
        system_prompt = "你是一位专业的小说创作助手。"

        if novel_settings and novel_settings.title:
            novel_type_cn = "科幻" if novel_settings.type == "scifi" else "玄幻"
            system_prompt += f"""

当前创作的小说信息:
- 标题: 《{novel_settings.title}》
- 类型: {novel_type_cn}
- 主角设定: {novel_settings.protagonist}
- 世界背景: {novel_settings.background}

请根据以上设定生成内容，注意：
1. 保持世界观和人物设定的一致性
2. 使用生动的描写和对话
3. 注意情节的连贯性和张力
4. 可以适当埋下伏笔和线索
5. 输出格式为流畅的中文小说文本
"""

        # 构建消息列表
        llm_messages = []

        # 添加系统提示词
        llm_messages.append(LLMMessage(role="system", content=system_prompt))

        # 添加历史消息（保留最近 10 条）
        if history:
            for msg in history[-10:]:
                llm_messages.append(LLMMessage(role=msg["role"], content=msg["content"]))

        # 添加当前用户消息
        llm_messages.append(LLMMessage(role="user", content=message))

        # 调用后端的流式生成
        async for chunk in llm_backend.generate_stream(
            messages=llm_messages,
            temperature=0.8,
            max_tokens=4000
        ):
            data = {
                "type": "text",
                "content": chunk
            }
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        # 发送结束信号
        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    except Exception as e:
        # 发送错误信息
        error_data = {
            "type": "text",
            "content": f"\n\n[错误: {str(e)}]"
        }
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"


@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天 API

    使用 Server-Sent Events (SSE) 实现流式响应

    接收参数:
    - message: 用户消息
    - novel_settings: 小说设定（可选）
    - history: 对话历史（可选）
    """
    try:
        return StreamingResponse(
            generate_stream_response(
                message=request.message,
                novel_settings=request.novel_settings,
                history=request.history
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/chat")
async def chat(request: ChatRequest):
    """
    普通聊天 API (非流式)

    如果不需要流式输出,可以使用这个端点
    """
    try:
        # TODO: 实现非流式响应
        # from claude_agent_sdk import query, ClaudeAgentOptions

        response_text = f"收到你的消息: \"{request.message}\""

        return {
            "role": "assistant",
            "content": response_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
