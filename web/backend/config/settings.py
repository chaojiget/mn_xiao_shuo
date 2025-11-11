"""
统一的配置管理系统

使用 pydantic-settings 管理所有配置，支持环境变量和 .env 文件。
所有模块应该从这里导入配置，而不是直接读取环境变量。
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类

    优先级：环境变量 > .env 文件 > 默认值
    """

    # ==================== LLM 配置 ====================
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # 默认模型：根据文档应该是 DeepSeek V3.1
    default_model: str = "deepseek/deepseek-v3.1-terminus"

    # 备选模型
    fallback_models: list[str] = [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
        "openai/gpt-4-turbo",
        "qwen/qwen-2.5-72b-instruct",
    ]

    # LLM 请求配置
    llm_timeout: int = 120
    llm_max_retries: int = 3
    llm_temperature: float = 0.7
    llm_max_tokens: int = 8000

    # ==================== 路径配置 ====================
    # 项目根目录（自动计算）
    @property
    def project_root(self) -> Path:
        """项目根目录"""
        return Path(__file__).parent.parent.parent.parent

    # 数据目录
    @property
    def data_dir(self) -> Path:
        """数据根目录"""
        return self.project_root / "data"

    @property
    def database_path(self) -> Path:
        """SQLite 数据库路径"""
        return self.data_dir / "sqlite" / "novel.db"

    @property
    def checkpoint_dir(self) -> Path:
        """检查点目录"""
        return self.data_dir / "checkpoints"

    @property
    def checkpoint_db_path(self) -> Path:
        """DM Agent 检查点数据库"""
        return self.checkpoint_dir / "dm.db"

    @property
    def quest_data_dir(self) -> Path:
        """任务数据目录"""
        return self.data_dir / "quests"

    @property
    def save_dir(self) -> Path:
        """游戏存档目录"""
        return self.data_dir / "saves"

    # 配置文件路径
    @property
    def config_dir(self) -> Path:
        """配置文件目录"""
        return self.project_root / "config"

    @property
    def llm_config_path(self) -> Path:
        """LLM 后端配置文件"""
        return self.config_dir / "llm_backend.yaml"

    @property
    def agent_config_path(self) -> Path:
        """Agent 配置文件"""
        return self.config_dir / "agent_config.yaml"

    # ==================== 数据库配置 ====================
    database_url: Optional[str] = None  # 如果设置则覆盖 database_path
    database_echo: bool = False  # SQLAlchemy echo
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # ==================== 服务器配置 ====================
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_reload: bool = True

    frontend_url: str = "http://localhost:3000"

    # CORS 配置
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ==================== 日志配置 ====================
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None  # 如果设置则写入文件

    # ==================== 游戏配置 ====================
    max_game_sessions: int = 100  # 最大并发游戏会话数
    session_timeout: int = 3600  # 会话超时时间（秒）
    auto_save_interval: int = 5  # 自动保存间隔（回合数）

    # ==================== 世界生成配置 ====================
    world_generation_model: Optional[str] = None  # 如果不设置则使用 default_model
    scene_refinement_passes: int = 4  # 场景细化的 Pass 数量

    # ==================== 向量/嵌入配置 ====================
    embedding_model: str = "qwen/qwen3-embedding-8b"  # 默认使用 Qwen3 Embedding 8B（OpenRouter）

    # ==================== 开发模式 ====================
    debug: bool = False
    enable_api_docs: bool = True  # 是否启用 /docs 和 /redoc

    # ==================== Agent 运行时 ====================
    dm_agent_backend: str = "langchain"  # langchain 或 langgraph（可通过 .env 覆盖）

    # ==================== 可选供应商/代理配置 ====================
    anthropic_base_url: Optional[str] = None
    anthropic_auth_token: Optional[str] = None
    anthropic_model: Optional[str] = None
    litellm_master_key: Optional[str] = None

    # pydantic-settings 配置
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # 忽略未定义的环境变量
    )

    def __init__(self, **kwargs):
        """初始化配置，创建必要的目录"""
        super().__init__(**kwargs)

        # 创建必要的目录
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.quest_data_dir.mkdir(parents=True, exist_ok=True)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "sqlite").mkdir(parents=True, exist_ok=True)

    @property
    def world_gen_model(self) -> str:
        """世界生成使用的模型"""
        return self.world_generation_model or self.default_model


# 全局配置实例
settings = Settings()


# 便捷访问函数
def get_settings() -> Settings:
    """获取配置实例（用于依赖注入）"""
    return settings


# 向后兼容：提供常用配置的快捷访问
def get_default_model() -> str:
    """获取默认模型"""
    return settings.default_model


def get_database_path() -> str:
    """获取数据库路径"""
    return str(settings.database_path)


def get_checkpoint_db_path() -> str:
    """获取检查点数据库路径"""
    return str(settings.checkpoint_db_path)
