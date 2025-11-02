"""
LiteLLM Proxy 后端实现
通过 LiteLLM Proxy 服务器调用 LLM
"""

import sys
import os
import httpx
from pathlib import Path
from typing import Dict, List, Any, Optional, AsyncIterator

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from .base import LLMBackend, LLMMessage, LLMTool, LLMResponse


class LiteLLMBackend(LLMBackend):
    """
    LiteLLM Proxy 后端适配器

    通过 LiteLLM Proxy 服务器调用 LLM，支持多种模型。
    需要先启动 LiteLLM Proxy: ./start_litellm_proxy.sh
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 LiteLLM Proxy 后端

        Args:
            config: 配置字典
              - proxy_url: LiteLLM Proxy 地址 (默认: http://localhost:4000)
              - api_key: Proxy API Key (从环境变量 LITELLM_MASTER_KEY 读取)
              - model: 默认模型名称 (默认: deepseek)
        """
        super().__init__(config)

        # Proxy 服务器地址
        self.proxy_url = self.config.get("proxy_url", os.environ.get("ANTHROPIC_BASE_URL", "http://localhost:4000"))

        # API Key (从环境变量读取)
        self.api_key = os.environ.get("LITELLM_MASTER_KEY", os.environ.get("ANTHROPIC_AUTH_TOKEN", ""))

        # 默认模型
        self.default_model = self.config.get("model", os.environ.get("ANTHROPIC_MODEL", "deepseek"))

        # 模型名称映射表（简写 -> 完整路径）
        # 注意：通过代理时，可以直接使用 model_list 中的 model_name
        self.model_map = {
            "deepseek": "deepseek",
            "claude-sonnet": "claude-sonnet",
            "claude-haiku": "claude-haiku",
            "gpt-4": "gpt-4",
            "qwen": "qwen",
        }

        # HTTP 客户端
        self.http_client = httpx.AsyncClient(
            base_url=self.proxy_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=120.0
        )

    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """
        生成文本响应

        Args:
            messages: 消息列表
            tools: 可用工具列表
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数(如model)

        Returns:
            LLMResponse: 响应对象
        """
        model = kwargs.get("model", self.default_model)

        # 提取系统消息和用户消息
        system_msg = None
        user_prompt = ""

        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            elif msg.role == "user":
                user_prompt += msg.content + "\n"

        # 如果提供了工具,使用结构化输出
        if tools:
            # 构建schema
            tool_schema = {
                "type": "object",
                "properties": {
                    "narration": {"type": "string"},
                    "tool_calls": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "arguments": {"type": "object"}
                            }
                        }
                    }
                },
                "required": ["narration"]
            }

            # 添加工具信息到提示
            tools_info = "\n\n".join([
                f"工具: {tool.name}\n描述: {tool.description}\n参数: {tool.input_schema}"
                for tool in tools
            ])
            enhanced_prompt = f"{user_prompt}\n\n可用工具:\n{tools_info}"

            result = await self.client.generate_structured(
                prompt=enhanced_prompt,
                schema=tool_schema,
                model=model,
                system=system_msg,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return LLMResponse(
                content=result.get("narration", ""),
                tool_calls=result.get("tool_calls", []),
                metadata={"model": model}
            )
        else:
            # 普通文本生成
            text = await self.client.generate(
                prompt=user_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system_msg
            )

            return LLMResponse(
                content=text,
                metadata={"model": model}
            )

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system: Optional[str] = None,
        tools: Optional[List[LLMTool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
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
            **kwargs: 其他参数(如model)

        Returns:
            Dict: 解析后的 JSON 对象
        """
        model = kwargs.get("model", self.default_model)

        # 如果有工具,添加到提示中
        if tools:
            tools_info = "\n\n".join([
                f"工具: {tool.name}\n描述: {tool.description}\n参数: {tool.input_schema}"
                for tool in tools
            ])
            enhanced_prompt = f"{prompt}\n\n可用工具:\n{tools_info}"
        else:
            enhanced_prompt = prompt

        result = await self.client.generate_structured(
            prompt=enhanced_prompt,
            schema=schema,
            model=model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return result

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        流式生成文本（通过 LiteLLM Proxy）

        Args:
            messages: 消息列表
            tools: 可用工具列表
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Yields:
            str: 文本片段
        """
        import json

        model = kwargs.get("model", self.default_model)

        # 将模型简写映射到实际名称
        actual_model = self.model_map.get(model, model)

        # 转换消息格式为 OpenAI 兼容格式
        api_messages = []
        for msg in messages:
            api_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # 构建请求体
        payload = {
            "model": actual_model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        # 发送流式请求到 LiteLLM Proxy
        # LiteLLM Proxy 支持 OpenAI 兼容的 /chat/completions 端点
        async with self.http_client.stream(
            "POST",
            "/chat/completions",
            json=payload
        ) as response:
            response.raise_for_status()

            # 读取 SSE 流
            async for line in response.aiter_lines():
                if not line or line.strip() == "":
                    continue

                # 跳过注释行
                if line.startswith(":"):
                    continue

                # 解析 SSE 数据
                if line.startswith("data: "):
                    data_str = line[6:]  # 移除 "data: " 前缀

                    # 检查是否是结束标记
                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                        # 提取 delta content
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError as e:
                        print(f"解析 JSON 失败: {e}, 数据: {data_str}")
                        continue

    def get_model_name(self) -> str:
        """获取当前使用的模型名称"""
        return self.default_model
