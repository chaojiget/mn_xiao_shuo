"""
Agent 配置加载器

支持从 YAML 配置文件加载多个 Agent 的配置,
每个 Agent 可以使用不同的模型和参数。

使用示例:
    loader = AgentConfigLoader()
    config = loader.get_agent_config("game_master")
    backend = create_backend_from_agent_config(config)
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class AgentConfigLoader:
    """Agent 配置加载器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径，默认为 config/llm_agents.yaml
        """
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            config_path = str(project_root / "config" / "llm_agents.yaml")

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_file = Path(self.config_path)

        if not config_file.exists():
            print(f"[WARNING] Agent配置文件不存在: {self.config_path}")
            print("[INFO] 返回空配置")
            return {"global": {}, "agents": {}}

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

    def get_global_config(self) -> Dict[str, Any]:
        """获取全局配置"""
        return self.config.get("global", {})

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        获取指定 Agent 的配置

        Args:
            agent_name: Agent 名称（如 "game_master", "npc_dialogue"等）

        Returns:
            Dict: Agent 配置，包含 backend, model, temperature 等
        """
        agents = self.config.get("agents", {})
        agent_config = agents.get(agent_name)

        if not agent_config:
            print(f"[WARNING] 未找到 Agent 配置: {agent_name}")
            print(f"[INFO] 可用的 Agent: {list(agents.keys())}")
            # 返回默认配置
            return {
                "backend": "litellm",
                "model": "deepseek",
                "temperature": 0.7,
                "max_tokens": 2000
            }

        # 合并全局配置
        global_config = self.get_global_config()
        merged_config = agent_config.copy()

        # 如果 Agent 使用 LiteLLM 代理,合并全局代理配置
        if merged_config.get("use_litellm_proxy"):
            if "litellm_base_url" not in merged_config:
                merged_config["litellm_base_url"] = global_config.get("litellm_proxy_url")
            if "litellm_auth_token" not in merged_config:
                merged_config["litellm_auth_token"] = global_config.get("litellm_master_key")

        return merged_config

    def list_agents(self) -> list:
        """列出所有可用的 Agent"""
        return list(self.config.get("agents", {}).keys())

    def print_agent_summary(self, agent_name: str):
        """打印 Agent 配置摘要"""
        config = self.get_agent_config(agent_name)

        print(f"\n{'='*60}")
        print(f"Agent 配置: {agent_name}")
        print(f"{'='*60}")
        print(f"后端: {config.get('backend', 'unknown')}")
        print(f"模型: {config.get('model', 'unknown')}")
        print(f"温度: {config.get('temperature', 0.7)}")
        print(f"最大Token: {config.get('max_tokens', 2000)}")

        if config.get("use_litellm_proxy"):
            print(f"使用代理: {config.get('litellm_base_url', 'unknown')}")

        allowed_tools = config.get("allowed_tools", [])
        print(f"允许的工具: {', '.join(allowed_tools) if allowed_tools else '无'}")

        system_prompt = config.get("system_prompt", "")
        if system_prompt:
            print(f"系统提示词: {system_prompt[:80]}...")

        print(f"{'='*60}\n")


def create_backend_from_agent_config(agent_config: Dict[str, Any]):
    """
    根据 Agent 配置创建 LLM 后端

    Args:
        agent_config: Agent 配置字典

    Returns:
        LLMBackend: 后端实例
    """
    from llm import create_backend

    backend_type = agent_config.get("backend", "litellm")
    return create_backend(backend_type, agent_config)


# 便捷函数
def load_agent_backend(agent_name: str, config_path: Optional[str] = None):
    """
    一键加载指定 Agent 的后端

    Args:
        agent_name: Agent 名称
        config_path: 配置文件路径（可选）

    Returns:
        LLMBackend: 后端实例

    使用示例:
        game_master = load_agent_backend("game_master")
        npc_agent = load_agent_backend("npc_dialogue")
    """
    loader = AgentConfigLoader(config_path)
    config = loader.get_agent_config(agent_name)
    loader.print_agent_summary(agent_name)
    return create_backend_from_agent_config(config)
