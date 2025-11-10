"""
统一的日志系统

提供统一的日志配置和获取方法。
所有模块应该使用 get_logger(__name__) 获取 logger，而不是 print() 或自己配置 logging。
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# 延迟导入 settings，避免循环依赖
_settings = None


def _get_settings():
    """延迟加载 settings"""
    global _settings
    if _settings is None:
        from config.settings import settings as s

        _settings = s
    return _settings


# 日志格式化器
class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器（适用于终端）"""

    # ANSI 颜色代码
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"

    def format(self, record):
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
            record.name = f"\033[90m{record.name}{self.RESET}"  # 灰色模块名

        return super().format(record)


# 全局配置标志
_configured = False


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    force: bool = False,
):
    """
    配置全局日志系统（应该在应用启动时调用一次）

    Args:
        log_level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        log_file: 日志文件路径（可选）
        log_format: 日志格式
        force: 是否强制重新配置
    """
    global _configured

    if _configured and not force:
        return

    settings = _get_settings()

    # 使用传入的参数或配置文件中的默认值
    level = log_level or settings.log_level
    format_str = log_format or settings.log_format
    file_path = log_file or settings.log_file

    # 获取根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # 清除已有的 handlers
    root_logger.handlers.clear()

    # 控制台 handler（彩色输出）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_formatter = ColoredFormatter(format_str)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 文件 handler（如果配置了）
    if file_path:
        log_path = Path(file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(getattr(logging, level.upper()))
        file_formatter = logging.Formatter(format_str)  # 文件不需要颜色
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    _configured = True

    # 记录日志系统已初始化
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统已初始化 (级别: {level})")
    if file_path:
        logger.info(f"日志文件: {file_path}")


def get_logger(name: str) -> logging.Logger:
    """
    获取 logger 实例

    Args:
        name: logger 名称，通常使用 __name__

    Returns:
        logging.Logger: logger 实例

    示例:
        ```python
        from utils.logger import get_logger

        logger = get_logger(__name__)
        logger.info("这是一条日志")
        ```
    """
    # 确保日志系统已初始化
    if not _configured:
        setup_logging()

    return logging.getLogger(name)


# 便捷函数：用于替换 print() 的场景
def log_info(message: str, logger_name: str = "app"):
    """记录 INFO 级别日志"""
    logger = get_logger(logger_name)
    logger.info(message)


def log_debug(message: str, logger_name: str = "app"):
    """记录 DEBUG 级别日志"""
    logger = get_logger(logger_name)
    logger.debug(message)


def log_warning(message: str, logger_name: str = "app"):
    """记录 WARNING 级别日志"""
    logger = get_logger(logger_name)
    logger.warning(message)


def log_error(message: str, logger_name: str = "app", exc_info: bool = False):
    """记录 ERROR 级别日志"""
    logger = get_logger(logger_name)
    logger.error(message, exc_info=exc_info)


def log_critical(message: str, logger_name: str = "app", exc_info: bool = False):
    """记录 CRITICAL 级别日志"""
    logger = get_logger(logger_name)
    logger.critical(message, exc_info=exc_info)


# 上下文管理器：临时改变日志级别
class LogLevel:
    """
    临时改变日志级别的上下文管理器

    示例:
        ```python
        with LogLevel("DEBUG"):
            # 这里的代码会使用 DEBUG 级别
            logger.debug("调试信息")
        # 这里恢复到原来的级别
        ```
    """

    def __init__(self, level: str):
        self.level = getattr(logging, level.upper())
        self.old_level = None

    def __enter__(self):
        root_logger = logging.getLogger()
        self.old_level = root_logger.level
        root_logger.setLevel(self.level)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        root_logger = logging.getLogger()
        root_logger.setLevel(self.old_level)
        return False


# 装饰器：记录函数调用
def log_function_call(logger: Optional[logging.Logger] = None):
    """
    装饰器：记录函数调用和返回值

    示例:
        ```python
        @log_function_call()
        def my_function(a, b):
            return a + b
        ```
    """
    import functools

    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 记录调用
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            logger.debug(f"调用 {func.__name__}({signature})")

            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} 返回 {result!r}")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} 抛出异常: {e}", exc_info=True)
                raise

        return wrapper

    return decorator
