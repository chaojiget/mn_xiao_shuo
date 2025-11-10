"""
LLM 后端配置加载器

注意：推荐使用 config.settings.Settings 来获取配置。
这个类主要用于加载 YAML 配置文件（向后兼容）。
"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml

from utils.logger import get_logger

logger = get_logger(__name__)


class LLMConfigLoader:
    """LLM 配置加载器"""

    def __init__(self, config_path: str = None):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径，默认为 config/llm_backend.yaml
        """
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            config_path = str(project_root / "config" / "llm_backend.yaml")

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_file = Path(self.config_path)

        if not config_file.exists():
            logger.warning(f"[WARNING] 配置文件不存在: {self.config_path}")
            # 使用统一的默认模型（DeepSeek，符合文档）
            default_model = os.getenv("DEFAULT_MODEL", "deepseek/deepseek-v3.1-terminus")
            logger.info(f"[INFO] 使用默认配置: LangChain + {default_model}")
            return {
                "backend": "langchain",
                "langchain": {"model": default_model, "temperature": 0.7},
            }

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 替换环境变量
        config = self._replace_env_vars(config)
        return config

    def _replace_env_vars(self, obj: Any) -> Any:
        """递归替换环境变量"""
        if isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            return os.getenv(env_var, "")
        return obj

    def get_backend_type(self) -> str:
        """获取后端类型"""
        return self.config.get("backend", "langchain")

    def get_backend_config(self, backend_type: str = None) -> Dict[str, Any]:
        """
        获取指定后端的配置

        Args:
            backend_type: 后端类型，默认使用配置文件中指定的

        Returns:
            Dict: 后端配置
        """
        if backend_type is None:
            backend_type = self.get_backend_type()

        return self.config.get(backend_type, {})

    def validate_config(self) -> bool:
        """
        验证配置是否有效

        Returns:
            bool: 配置是否有效
        """
        backend_type = self.get_backend_type()

        if backend_type not in ["litellm", "claude"]:
            logger.error(f"[ERROR] 无效的后端类型: {backend_type}")
            return False

        if backend_type == "claude":
            # 检查是否有 API key
            api_key = self.config.get("claude", {}).get("api_key")
            if not api_key:
                logger.error("[ERROR] Claude 后端需要设置 ANTHROPIC_API_KEY")
                return False

        return True

    def print_config_summary(self):
        """打印配置摘要"""
        backend_type = self.get_backend_type()
        backend_config = self.get_backend_config()

        logger.info(f"\n{'='*50}")
        logger.info(f"LLM 后端配置")
        logger.info(f"{'='*50}")
        logger.info(f"后端类型: {backend_type}")

        if backend_type == "langchain":
            default_model = os.getenv("DEFAULT_MODEL", "deepseek/deepseek-v3.1-terminus")
            logger.info(f"默认模型: {backend_config.get('model', default_model)}")
            logger.info(f"温度: {backend_config.get('temperature', 0.7)}")
            logger.info(f"成本: 低 (~$0.001-0.005/回合)")
        elif backend_type == "litellm":
            logger.warning(f"⚠️  LiteLLM 已被移除，请使用 LangChain")
            logger.info(f"默认模型: {backend_config.get('model', 'deepseek')}")
        elif backend_type == "claude":
            logger.info(f"模型: {backend_config.get('model', 'claude-sonnet-4')}")
            logger.info(f"成本: 高 (~$0.015/回合)")

        logger.info(f"{'='*50}\n")
