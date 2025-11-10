"""
LLM 后端抽象层 - LangChain 1.0 实现
"""

from .base import LLMBackend, LLMMessage, LLMResponse, LLMTool
from .langchain_backend import LangChainBackend

__all__ = [
    "LLMBackend",
    "LLMMessage",
    "LLMTool",
    "LLMResponse",
    "LangChainBackend",
]


def create_backend(backend_type: str = "langchain", config: dict = None) -> LLMBackend:
    """
    工厂函数：创建 LLM 后端实例

    Args:
        backend_type: 后端类型 (目前只支持 "langchain")
        config: 配置字典

    Returns:
        LLMBackend: 后端实例

    Raises:
        ValueError: 不支持的后端类型
    """
    if backend_type == "langchain":
        return LangChainBackend(config)
    else:
        raise ValueError(f"不支持的后端类型: {backend_type}，目前只支持 'langchain'")


def get_available_backends() -> dict:
    """获取可用的后端列表"""
    return {
        "langchain": {
            "available": True,
            "description": "LangChain 1.0 + OpenRouter - 支持多种模型",
            "cost": "中",
            "models": ["deepseek", "claude-sonnet", "claude-haiku", "gpt-4", "qwen"],
            "features": ["streaming", "tools", "structured_output"],
        }
    }
