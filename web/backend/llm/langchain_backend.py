"""
LangChain 后端实现 (通过 OpenRouter)
从 LiteLLM + Claude Agent SDK 迁移到 LangChain 1.0
"""

import asyncio
import json
import os
from typing import Any, AsyncIterator, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from config.settings import settings

from utils.logger import get_logger

from .base import LLMBackend, LLMMessage, LLMResponse, LLMTool

logger = get_logger(__name__)


class LangChainBackend(LLMBackend):
    """
    LangChain 后端 (通过 OpenRouter)

    支持:
    1. 通过 OpenRouter 调用多种模型 (DeepSeek, Claude, GPT-4, Qwen)
    2. 流式生成
    3. 工具调用
    4. 结构化输出

    配置示例:
    {
        "model": "deepseek",  # 或 "deepseek/deepseek-v3.1-terminus"
        "temperature": 0.7,
        "max_tokens": 4096,
        "streaming": True
    }
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 LangChain 后端

        Args:
            config: 配置字典
              - model: 模型名称 (支持简写)
              - temperature: 温度参数 (默认 0.7)
              - max_tokens: 最大token数 (默认 4096)
              - streaming: 是否启用流式 (默认 True)
        """
        super().__init__(config)

        # 模型名称映射
        self.model_map = {
            "deepseek": "deepseek/deepseek-v3.1-terminus",
            "claude-sonnet": "anthropic/claude-3.5-sonnet",
            "claude-haiku": "anthropic/claude-3-haiku",
            "gpt-4": "openai/gpt-4-turbo",
            "qwen": "qwen/qwen-2.5-72b-instruct",
            "kimi": "deepseek/deepseek-v3.1-terminus",
        }

        # 获取模型名称（统一从 settings.default_model，可被 config 覆盖）
        model_key = self.config.get("model", settings.default_model)
        model_name = self.model_map.get(model_key, model_key)

        # 初始化 ChatOpenAI (OpenRouter)
        self.model = ChatOpenAI(
            model=model_name,
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            temperature=self.config.get("temperature", settings.llm_temperature),
            max_tokens=self.config.get("max_tokens", min(settings.llm_max_tokens, 4096)),
            streaming=self.config.get("streaming", True),
        )

        logger.info(f"[LangChainBackend] 初始化完成，模型: {model_name}")

    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> LLMResponse:
        """
        生成文本响应

        Args:
            messages: 消息列表
            tools: 可用工具列表
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            LLMResponse: 响应对象
        """
        # 转换消息格式
        lc_messages = self._convert_messages(messages)

        # 配置模型
        model = self.model.with_config(temperature=temperature, max_tokens=max_tokens)

        # 如果提供了工具,绑定工具
        if tools:
            lc_tools = self._convert_tools(tools)
            model = model.bind_tools(lc_tools)

        # 调用模型
        response = await model.ainvoke(lc_messages)

        # 解析响应
        content = response.content if isinstance(response.content, str) else ""
        tool_calls = []

        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_calls = [
                {"name": tc.get("name"), "arguments": tc.get("args", {})}
                for tc in response.tool_calls
            ]

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            metadata={"model": self.model.model_name, "backend": "LangChain"},
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system: Optional[str] = None,
        tools: Optional[List[LLMTool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        生成结构化 JSON 输出

        Args:
            prompt: 用户提示
            schema: JSON schema
            system: 系统提示
            tools: 可用工具列表
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            Dict: 解析后的 JSON 对象
        """
        # 构建消息
        messages = []
        if system:
            messages.append(SystemMessage(content=system))

        # 添加 JSON schema 要求到提示词
        json_instruction = f"""
请严格按照以下 JSON schema 返回结果:
```json
{json.dumps(schema, indent=2, ensure_ascii=False)}
```

只返回有效的 JSON，不要有其他文字。
"""
        combined_prompt = prompt + "\n\n" + json_instruction
        messages.append(HumanMessage(content=combined_prompt))

        # 调用模型
        model = self.model.with_config(temperature=temperature, max_tokens=max_tokens)
        response = await model.ainvoke(messages)

        # 解析 JSON
        try:
            content = response.content.strip()

            # 移除可能的 markdown 代码块标记
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"无法解析 JSON 响应: {e}\n响应内容: {response.content}")

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        cancel_event: Optional[asyncio.Event] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        流式生成文本（支持取消和错误处理）

        Args:
            messages: 消息列表
            tools: 可用工具列表
            temperature: 温度参数
            max_tokens: 最大token数
            cancel_event: 取消事件（设置后将停止生成）
            **kwargs: 其他参数

        Yields:
            str: 文本片段

        Raises:
            asyncio.CancelledError: 生成被取消
            Exception: 其他错误
        """
        try:
            # 转换消息格式
            lc_messages = self._convert_messages(messages)

            # 配置模型
            model = self.model.with_config(temperature=temperature, max_tokens=max_tokens)

            # 如果提供了工具,绑定工具
            if tools:
                lc_tools = self._convert_tools(tools)
                model = model.bind_tools(lc_tools)

            # 流式调用
            async for chunk in model.astream(lc_messages):
                # 检查取消事件
                if cancel_event and cancel_event.is_set():
                    logger.info("[LangChainBackend] 流式生成已取消")
                    raise asyncio.CancelledError("流式生成被用户取消")

                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content

        except asyncio.CancelledError:
            logger.info("[LangChainBackend] 流式生成被取消")
            raise

        except Exception as e:
            logger.error(f"[LangChainBackend] 流式生成错误: {str(e)}")
            # 重新抛出异常，让调用者处理
            raise

    def _convert_messages(self, messages: List[LLMMessage]) -> List:
        """转换消息格式"""
        lc_messages = []
        for msg in messages:
            if msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))
        return lc_messages

    def _convert_tools(self, tools: List[LLMTool]) -> List[Dict[str, Any]]:
        """转换工具格式"""
        # LangChain 期望的工具格式
        lc_tools = []
        for tool in tools:
            lc_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
            )
        return lc_tools

    def get_model_name(self) -> str:
        """获取当前使用的模型名称"""
        return self.model.model_name

    def get_backend_info(self) -> Dict[str, Any]:
        """获取后端信息"""
        from config.settings import settings
        return {
            "backend": "LangChain",
            "model": self.model.model_name,
            "provider": "OpenRouter",
            "supports_streaming": True,
            "supports_tools": True,
            "base_url": settings.openrouter_base_url,
        }
