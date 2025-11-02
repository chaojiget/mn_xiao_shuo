"""
LLM 后端抽象层 - 支持多种 LLM 后端
"""

from .base import LLMBackend, LLMMessage, LLMTool, LLMResponse
from .litellm_backend import LiteLLMBackend

# Claude 后端是可选的，需要安装 anthropic 包
try:
    from .claude_backend import ClaudeBackend
    _CLAUDE_AVAILABLE = True
except ImportError:
    ClaudeBackend = None  # type: ignore
    _CLAUDE_AVAILABLE = False

__all__ = [
    "LLMBackend",
    "LLMMessage",
    "LLMTool",
    "LLMResponse",
    "LiteLLMBackend",
    "ClaudeBackend",
]


def create_backend(backend_type: str = "litellm", config: dict = None) -> LLMBackend:
    """
    工厂函数：创建 LLM 后端实例

    Args:
        backend_type: 后端类型 ("litellm" 或 "claude")
        config: 配置字典

    Returns:
        LLMBackend: 后端实例

    Raises:
        ValueError: 不支持的后端类型
        ImportError: Claude 后端未安装
    """
    if backend_type == "litellm":
        return LiteLLMBackend(config)
    elif backend_type == "claude":
        if not _CLAUDE_AVAILABLE:
            raise ImportError(
                "Claude 后端需要安装 anthropic 包\n"
                "运行: uv pip install anthropic"
            )
        return ClaudeBackend(config)
    else:
        raise ValueError(f"不支持的后端类型: {backend_type}")


def get_available_backends() -> dict:
    """获取可用的后端列表"""
    return {
        "litellm": {
            "available": True,
            "description": "LiteLLM - 支持多种模型 (DeepSeek, Claude, GPT等)",
            "cost": "低",
            "models": ["deepseek", "claude-sonnet", "claude-haiku", "gpt-4", "qwen"]
        },
        "claude": {
            "available": _CLAUDE_AVAILABLE,
            "description": "Claude Agent SDK - Anthropic 官方实现",
            "cost": "高",
            "models": ["claude-sonnet-4", "claude-opus-4", "claude-haiku-3.5"],
            "requires": "anthropic" if not _CLAUDE_AVAILABLE else None
        }
    }
