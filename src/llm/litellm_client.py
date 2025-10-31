"""LiteLLM 统一客户端"""

import os
import yaml
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

import litellm
from litellm import Router


class LiteLLMClient:
    """LiteLLM 统一客户端 - 支持多个LLM提供商的统一接口"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化 LiteLLM 客户端

        Args:
            config_path: 配置文件路径,默认从环境变量获取
        """
        if config_path is None:
            config_path = os.getenv(
                "LITELLM_CONFIG_PATH",
                "./config/litellm_config.yaml"
            )

        self.config_path = config_path
        self.config = self._load_config()
        self.router = self._create_router()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

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

    def _create_router(self) -> Router:
        """创建 LiteLLM Router"""
        model_list = self.config.get("model_list", [])
        router_settings = self.config.get("router_settings", {})

        router = Router(
            model_list=model_list,
            **router_settings
        )

        return router

    async def generate(
        self,
        prompt: str,
        model: str = "claude-sonnet",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        生成文本

        Args:
            prompt: 用户提示词
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            system: 系统提示词
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.router.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        return response.choices[0].message.content

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: str = "claude-sonnet",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成结构化输出(JSON)

        Args:
            prompt: 用户提示词
            schema: JSON Schema
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            system: 系统提示词
            **kwargs: 其他参数

        Returns:
            解析后的 JSON 对象
        """
        # 构建包含 schema 的提示
        schema_prompt = f"""{prompt}

请严格按照以下 JSON Schema 返回结果:
```json
{json.dumps(schema, ensure_ascii=False, indent=2)}
```

只返回 JSON,不要包含任何其他文本。
"""

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": schema_prompt})

        response = await self.router.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        content = response.choices[0].message.content.strip()

        # 尝试提取 JSON
        if "```json" in content:
            # 提取代码块中的 JSON
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        elif "```" in content:
            json_start = content.find("```") + 3
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"无法解析 JSON 响应: {content}\n错误: {e}")

    async def generate_with_functions(
        self,
        prompt: str,
        functions: List[Dict[str, Any]],
        model: str = "claude-sonnet",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用函数调用生成

        Args:
            prompt: 用户提示词
            functions: 函数定义列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            system: 系统提示词
            **kwargs: 其他参数

        Returns:
            包含函数调用的响应
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.router.acompletion(
            model=model,
            messages=messages,
            functions=functions,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        return {
            "content": response.choices[0].message.content,
            "function_call": response.choices[0].message.function_call
            if hasattr(response.choices[0].message, "function_call")
            else None,
        }

    async def batch_generate(
        self,
        prompts: List[str],
        model: str = "claude-haiku",  # 批量任务使用快速模型
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> List[str]:
        """
        批量生成

        Args:
            prompts: 提示词列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            生成的文本列表
        """
        import asyncio

        tasks = [
            self.generate(p, model, temperature, max_tokens, **kwargs)
            for p in prompts
        ]

        return await asyncio.gather(*tasks)

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """获取模型信息"""
        for model in self.config.get("model_list", []):
            if model.get("model_name") == model_name:
                return model
        return None

    def list_models(self) -> List[str]:
        """列出所有可用模型"""
        return [m["model_name"] for m in self.config.get("model_list", [])]
