"""
统一的异常处理系统

定义项目中使用的所有自定义异常类。
所有模块应该使用这些异常类，而不是直接抛出 Exception。
"""

from typing import Any, Dict, Optional

# ==================== 基础异常 ====================


class AppException(Exception):
    """应用基础异常类

    所有自定义异常都应该继承这个类。
    """

    def __init__(
        self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            message: 错误消息
            code: 错误代码（用于客户端判断）
            details: 错误详情（额外信息）
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于 API 响应）"""
        return {"error": self.code, "message": self.message, "details": self.details}


# ==================== 配置相关异常 ====================


class ConfigurationError(AppException):
    """配置错误"""

    pass


class MissingConfigError(ConfigurationError):
    """缺少必需的配置"""

    pass


class InvalidConfigError(ConfigurationError):
    """配置值无效"""

    pass


# ==================== 数据库相关异常 ====================


class DatabaseError(AppException):
    """数据库错误基类"""

    pass


class DatabaseConnectionError(DatabaseError):
    """数据库连接错误"""

    pass


class RecordNotFoundError(DatabaseError):
    """记录未找到"""

    def __init__(self, model: str, identifier: Any):
        super().__init__(
            message=f"{model} 未找到: {identifier}",
            code="RECORD_NOT_FOUND",
            details={"model": model, "identifier": str(identifier)},
        )


class RecordAlreadyExistsError(DatabaseError):
    """记录已存在"""

    def __init__(self, model: str, identifier: Any):
        super().__init__(
            message=f"{model} 已存在: {identifier}",
            code="RECORD_ALREADY_EXISTS",
            details={"model": model, "identifier": str(identifier)},
        )


class DatabaseIntegrityError(DatabaseError):
    """数据库完整性错误（如外键约束失败）"""

    pass


# ==================== LLM 相关异常 ====================


class LLMError(AppException):
    """LLM 错误基类"""

    pass


class LLMConnectionError(LLMError):
    """LLM 连接错误"""

    pass


class LLMTimeoutError(LLMError):
    """LLM 请求超时"""

    pass


class LLMRateLimitError(LLMError):
    """LLM 速率限制"""

    def __init__(self, message: str = "API 速率限制", retry_after: Optional[int] = None):
        super().__init__(message=message, code="RATE_LIMIT", details={"retry_after": retry_after})
        self.retry_after = retry_after


class LLMInvalidResponseError(LLMError):
    """LLM 返回无效响应"""

    def __init__(self, message: str, response: Optional[str] = None):
        super().__init__(
            message=message, code="INVALID_LLM_RESPONSE", details={"response": response}
        )


class LLMModelNotFoundError(LLMError):
    """LLM 模型未找到"""

    def __init__(self, model: str):
        super().__init__(
            message=f"模型未找到: {model}", code="MODEL_NOT_FOUND", details={"model": model}
        )


# ==================== 游戏引擎相关异常 ====================


class GameEngineError(AppException):
    """游戏引擎错误基类"""

    pass


class GameStateNotFoundError(GameEngineError):
    """游戏状态未找到"""

    def __init__(self, session_id: str):
        super().__init__(
            message=f"游戏状态未找到: {session_id}",
            code="GAME_STATE_NOT_FOUND",
            details={"session_id": session_id},
        )


class InvalidGameActionError(GameEngineError):
    """无效的游戏操作"""

    def __init__(self, action: str, reason: str):
        super().__init__(
            message=f"无效的游戏操作: {action} ({reason})",
            code="INVALID_GAME_ACTION",
            details={"action": action, "reason": reason},
        )


class GameSessionExpiredError(GameEngineError):
    """游戏会话已过期"""

    def __init__(self, session_id: str):
        super().__init__(
            message=f"游戏会话已过期: {session_id}",
            code="SESSION_EXPIRED",
            details={"session_id": session_id},
        )


class MaxSessionsReachedError(GameEngineError):
    """达到最大会话数"""

    def __init__(self, max_sessions: int):
        super().__init__(
            message=f"达到最大会话数限制: {max_sessions}",
            code="MAX_SESSIONS_REACHED",
            details={"max_sessions": max_sessions},
        )


# ==================== 世界生成相关异常 ====================


class WorldGenerationError(AppException):
    """世界生成错误基类"""

    pass


class InvalidWorldConfigError(WorldGenerationError):
    """无效的世界配置"""

    pass


class SceneRefinementError(WorldGenerationError):
    """场景细化错误"""

    def __init__(self, pass_name: str, reason: str):
        super().__init__(
            message=f"场景细化失败 (Pass: {pass_name}): {reason}",
            code="SCENE_REFINEMENT_ERROR",
            details={"pass": pass_name, "reason": reason},
        )


# ==================== 存档相关异常 ====================


class SaveError(AppException):
    """存档错误基类"""

    pass


class SaveNotFoundError(SaveError):
    """存档未找到"""

    def __init__(self, save_id: str):
        super().__init__(
            message=f"存档未找到: {save_id}", code="SAVE_NOT_FOUND", details={"save_id": save_id}
        )


class SaveCorruptedError(SaveError):
    """存档已损坏"""

    def __init__(self, save_id: str, reason: str):
        super().__init__(
            message=f"存档已损坏: {save_id} ({reason})",
            code="SAVE_CORRUPTED",
            details={"save_id": save_id, "reason": reason},
        )


class SaveSlotFullError(SaveError):
    """存档槽位已满"""

    def __init__(self, slot_id: int):
        super().__init__(
            message=f"存档槽位 {slot_id} 已存在，请先删除或使用覆盖选项",
            code="SAVE_SLOT_FULL",
            details={"slot_id": slot_id},
        )


# ==================== Agent 相关异常 ====================


class AgentError(AppException):
    """Agent 错误基类"""

    pass


class AgentInitializationError(AgentError):
    """Agent 初始化错误"""

    pass


class AgentToolError(AgentError):
    """Agent 工具执行错误"""

    def __init__(self, tool_name: str, reason: str):
        super().__init__(
            message=f"工具执行失败: {tool_name} ({reason})",
            code="AGENT_TOOL_ERROR",
            details={"tool": tool_name, "reason": reason},
        )


class AgentCheckpointError(AgentError):
    """Agent 检查点错误"""

    pass


# ==================== 验证相关异常 ====================


class ValidationError(AppException):
    """验证错误"""

    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"验证失败: {field} - {message}",
            code="VALIDATION_ERROR",
            details={"field": field},
        )


# ==================== 辅助函数 ====================


def handle_exception(exc: Exception) -> Dict[str, Any]:
    """
    统一处理异常，返回标准化的错误响应

    Args:
        exc: 异常对象

    Returns:
        错误响应字典
    """
    if isinstance(exc, AppException):
        return exc.to_dict()
    else:
        # 未知异常
        return {"error": "INTERNAL_ERROR", "message": str(exc), "details": {}}
