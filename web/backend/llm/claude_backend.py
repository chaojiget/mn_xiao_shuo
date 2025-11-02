"""
Claude Agent SDK 后端实现 (通过 LiteLLM 代理)

这个后端使用 Claude Agent SDK 的 Agent 能力（工具、Hook等）,
但通过 LiteLLM 代理来调用不同的模型（DeepSeek, GPT, Qwen等）

架构:
  ClaudeAgentSDK → LiteLLM Proxy (port 4000) → DeepSeek/GPT/Qwen/etc.

需要安装: pip install claude-agent-sdk

环境变量:
  ANTHROPIC_BASE_URL="http://0.0.0.0:4000"  # LiteLLM 代理地址
  ANTHROPIC_AUTH_TOKEN="sk-litellm-..."     # LiteLLM master key
  LITELLM_MASTER_KEY="sk-litellm-..."       # LiteLLM master key
"""

import os
import json
from typing import Dict, List, Any, Optional, AsyncIterator
from .base import LLMBackend, LLMMessage, LLMTool, LLMResponse


class ClaudeBackend(LLMBackend):
    """
    Claude Agent SDK 后端 (通过 LiteLLM 代理)

    支持:
    1. 直接调用 Claude API (设置 ANTHROPIC_API_KEY)
    2. 通过 LiteLLM 代理调用任意模型 (设置 ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN)

    配置示例:
    {
        "use_litellm_proxy": True,
        "litellm_base_url": "http://0.0.0.0:4000",
        "litellm_auth_token": "sk-litellm-...",
        "model": "deepseek",  # 或任何 LiteLLM 配置的模型
        "allowed_tools": ["Read", "Write", "Bash"]
    }
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 Claude Agent SDK 后端

        Args:
            config: 配置字典
              - use_litellm_proxy: 是否使用 LiteLLM 代理 (默认 False)
              - litellm_base_url: LiteLLM 代理地址 (默认 http://0.0.0.0:4000)
              - litellm_auth_token: LiteLLM 认证 token
              - api_key: Anthropic API 密钥 (不使用代理时)
              - model: 模型名称
              - max_tokens: 最大token数
              - cwd: 工作目录
              - allowed_tools: 允许的工具列表
        """
        super().__init__(config)

        # 导入 claude-agent-sdk
        try:
            from claude_agent_sdk import (
                query,
                ClaudeAgentOptions,
                ClaudeSDKClient,
                AssistantMessage,
                TextBlock,
                ToolUseBlock
            )
            self.query_func = query
            self.ClaudeAgentOptions = ClaudeAgentOptions
            self.ClaudeSDKClient = ClaudeSDKClient
            self.AssistantMessage = AssistantMessage
            self.TextBlock = TextBlock
            self.ToolUseBlock = ToolUseBlock
        except ImportError:
            raise ImportError(
                "需要安装 claude-agent-sdk 包: pip install claude-agent-sdk\n"
                "这是Anthropic官方的Agent SDK"
            )

        # 检查是否使用 LiteLLM 代理
        use_litellm_proxy = self.config.get("use_litellm_proxy", False)

        if use_litellm_proxy:
            # 使用 LiteLLM 代理模式
            litellm_base_url = self.config.get("litellm_base_url") or os.getenv("LITELLM_BASE_URL", "http://0.0.0.0:4000")
            litellm_auth_token = self.config.get("litellm_auth_token") or os.getenv("LITELLM_MASTER_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")

            if not litellm_auth_token:
                raise ValueError(
                    "使用 LiteLLM 代理需要设置 LITELLM_MASTER_KEY 或 ANTHROPIC_AUTH_TOKEN\n"
                    "例如: export LITELLM_MASTER_KEY=sk-litellm-..."
                )

            # 设置环境变量让 Claude Agent SDK 使用 LiteLLM 代理
            os.environ["ANTHROPIC_BASE_URL"] = litellm_base_url
            os.environ["ANTHROPIC_AUTH_TOKEN"] = litellm_auth_token

            print(f"[INFO] Claude Agent SDK 使用 LiteLLM 代理: {litellm_base_url}")

            # 模型名称（可以是 LiteLLM 配置的任何模型）
            self.default_model = self.config.get("model", "deepseek")
        else:
            # 直接使用 Claude API
            api_key = self.config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "未设置 ANTHROPIC_API_KEY\n"
                    "请在 .env 文件中设置或传入 config"
                )

            os.environ["ANTHROPIC_API_KEY"] = api_key
            self.default_model = self.config.get("model", "claude-sonnet-4-20250514")

        self.default_max_tokens = self.config.get("max_tokens", 4096)
        self.cwd = self.config.get("cwd")
        self.allowed_tools = self.config.get("allowed_tools", [])

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
            **kwargs: 其他参数

        Returns:
            LLMResponse: 响应对象
        """
        # 构建系统提示词和用户消息
        system_prompt = None
        user_messages = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                user_messages.append(f"{msg.role}: {msg.content}")

        # 合并消息为单个提示
        prompt = "\n\n".join(user_messages)

        # 准备选项
        options_dict = {
            "max_turns": 1,  # 单轮对话
        }

        if system_prompt:
            options_dict["system_prompt"] = system_prompt

        if self.cwd:
            options_dict["cwd"] = self.cwd

        if tools or self.allowed_tools:
            # 如果提供了工具,启用相应的工具
            tool_names = self.allowed_tools.copy()
            if tools:
                # 映射自定义工具(这里简化处理,实际需要MCP server)
                tool_names.extend(["Read", "Write", "Bash"])  # 默认工具
            options_dict["allowed_tools"] = list(set(tool_names))

        options = self.ClaudeAgentOptions(**options_dict)

        # 调用 Claude Agent SDK
        response_content = ""
        tool_calls = []

        async for message in self.query_func(prompt=prompt, options=options):
            if isinstance(message, self.AssistantMessage):
                for block in message.content:
                    if isinstance(block, self.TextBlock):
                        response_content += block.text
                    elif isinstance(block, self.ToolUseBlock):
                        tool_calls.append({
                            "name": block.name,
                            "arguments": block.input
                        })

        return LLMResponse(
            content=response_content,
            tool_calls=tool_calls,
            metadata={
                "model": self.default_model,
                "backend": "claude-agent-sdk"
            }
        )

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_schema: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成结构化 JSON 输出

        Args:
            messages: 消息列表
            response_schema: JSON schema
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            Dict: 解析后的JSON对象
        """
        # 构建强制 JSON 输出的提示
        system_prompt = None
        user_messages = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                user_messages.append(msg.content)

        # 添加 JSON schema 要求
        json_instruction = f"""
请严格按照以下 JSON schema 返回结果:
```json
{json.dumps(response_schema, indent=2, ensure_ascii=False)}
```

只返回有效的 JSON，不要有其他文字。
"""

        combined_prompt = "\n\n".join(user_messages) + "\n\n" + json_instruction

        # 准备选项
        options_dict = {
            "max_turns": 1,
        }

        if system_prompt:
            options_dict["system_prompt"] = system_prompt

        options = self.ClaudeAgentOptions(**options_dict)

        # 调用 Claude Agent SDK
        response_content = ""

        async for message in self.query_func(prompt=combined_prompt, options=options):
            if isinstance(message, self.AssistantMessage):
                for block in message.content:
                    if isinstance(block, self.TextBlock):
                        response_content += block.text

        # 解析 JSON
        try:
            # 移除可能的 markdown 代码块标记
            content = response_content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"无法解析 JSON 响应: {e}\n响应内容: {response_content}")

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        流式生成文本

        注意: claude-agent-sdk 的 query 本身就是异步迭代器

        Args:
            messages: 消息列表
            tools: 可用工具列表
            temperature: 温度参数
            max_tokens: 最大token数

        Yields:
            str: 文本片段
        """
        # 构建提示
        system_prompt = None
        user_messages = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                user_messages.append(f"{msg.role}: {msg.content}")

        prompt = "\n\n".join(user_messages)

        # 准备选项
        options_dict = {
            "max_turns": 1,
        }

        if system_prompt:
            options_dict["system_prompt"] = system_prompt

        if self.cwd:
            options_dict["cwd"] = self.cwd

        if tools or self.allowed_tools:
            tool_names = self.allowed_tools.copy()
            if tools:
                tool_names.extend(["Read", "Write", "Bash"])
            options_dict["allowed_tools"] = list(set(tool_names))

        options = self.ClaudeAgentOptions(**options_dict)

        # 流式调用
        async for message in self.query_func(prompt=prompt, options=options):
            if isinstance(message, self.AssistantMessage):
                for block in message.content:
                    if isinstance(block, self.TextBlock):
                        # 流式输出文本
                        yield block.text

    def get_model_name(self) -> str:
        """获取当前使用的模型名称"""
        return self.default_model

    def get_backend_info(self) -> Dict[str, Any]:
        """获取后端信息"""
        return {
            "backend": "ClaudeAgentSDK",
            "model": self.default_model,
            "provider": "Anthropic",
            "supports_streaming": True,
            "supports_tools": True,
            "supports_hooks": True,
            "sdk": "claude-agent-sdk (官方)",
            "cost_tier": "premium"  # Claude 成本较高
        }
