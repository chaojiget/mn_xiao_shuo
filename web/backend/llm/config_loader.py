"""
LLM 后端配置加载器
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


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
            print(f"[WARNING] 配置文件不存在: {self.config_path}")
            print("[INFO] 使用默认配置: LangChain + DeepSeek")
            return {
                "backend": "langchain",
                "langchain": {
                    "model": "deepseek/deepseek-v3.1-terminus",
                    "temperature": 0.7
                }
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
            print(f"[ERROR] 无效的后端类型: {backend_type}")
            return False

        if backend_type == "claude":
            # 检查是否有 API key
            api_key = self.config.get("claude", {}).get("api_key")
            if not api_key:
                print("[ERROR] Claude 后端需要设置 ANTHROPIC_API_KEY")
                return False

        return True

    def print_config_summary(self):
        """打印配置摘要"""
        backend_type = self.get_backend_type()
        backend_config = self.get_backend_config()

        print(f"\n{'='*50}")
        print(f"LLM 后端配置")
        print(f"{'='*50}")
        print(f"后端类型: {backend_type}")

        if backend_type == "langchain":
            print(f"默认模型: {backend_config.get('model', 'deepseek/deepseek-v3.1-terminus')}")
            print(f"温度: {backend_config.get('temperature', 0.7)}")
            print(f"成本: 低 (~$0.001/回合)")
        elif backend_type == "litellm":
            print(f"⚠️  LiteLLM 已被移除，请使用 LangChain")
            print(f"默认模型: {backend_config.get('model', 'deepseek')}")
        elif backend_type == "claude":
            print(f"模型: {backend_config.get('model', 'claude-sonnet-4')}")
            print(f"成本: 高 (~$0.015/回合)")

        print(f"{'='*50}\n")
