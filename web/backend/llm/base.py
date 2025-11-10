"""
LLM 后端抽象基类
定义统一接口，支持不同的 LLM 实现
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel


class LLMMessage(BaseModel):
    """LLM 消息"""

    role: str  # system, user, assistant
    content: str


class LLMTool(BaseModel):
    """LLM 工具定义"""

    name: str
    description: str
    input_schema: Dict[str, Any]


class LLMResponse(BaseModel):
    """LLM 响应"""

    content: str  # 生成的文本
    tool_calls: List[Dict[str, Any]] = []  # 工具调用
    metadata: Dict[str, Any] = {}  # 元数据(tokens, cost等)


class LLMBackend(ABC):
    """LLM 后端抽象基类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 LLM 后端

        Args:
            config: 配置字典
        """
        self.config = config or {}

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        流式生成文本

        Args:
            messages: 消息列表
            tools: 可用工具列表
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Yields:
            str: 文本片段
        """
        pass

    def get_model_name(self) -> str:
        """获取当前使用的模型名称"""
        return self.config.get("model", "unknown")

    def get_backend_info(self) -> Dict[str, Any]:
        """获取后端信息"""
        return {
            "backend": self.__class__.__name__,
            "model": self.get_model_name(),
            "config": self.config,
        }
