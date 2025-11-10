# 代码规范与最佳实践

**更新日期**: 2025-11-09
**适用范围**: AI 小说生成系统后端代码

---

## 目录

1. [配置管理](#配置管理)
2. [日志记录](#日志记录)
3. [错误处理](#错误处理)
4. [路径处理](#路径处理)
5. [导入规范](#导入规范)
6. [代码风格](#代码风格)
7. [类型注解](#类型注解)
8. [文档字符串](#文档字符串)

---

## 配置管理

### ✅ 推荐做法

```python
# 使用统一的配置系统
from config.settings import settings

# 访问配置
model = settings.default_model
db_path = settings.database_path
log_level = settings.log_level

# 在函数中使用依赖注入（FastAPI）
from fastapi import Depends
from config.settings import get_settings, Settings

@app.get("/info")
async def get_info(config: Settings = Depends(get_settings)):
    return {"model": config.default_model}
```

### ❌ 不推荐做法

```python
# 不要直接读取环境变量
import os
model = os.getenv("DEFAULT_MODEL", "some-fallback")

# 不要硬编码配置
model = "deepseek/deepseek-v3.1-terminus"
db_path = "data/sqlite/novel.db"
```

### 配置优先级

1. 环境变量（最高优先级）
2. `.env` 文件
3. `settings.py` 中的默认值（最低优先级）

### 添加新配置

```python
# 1. 在 config/settings.py 中添加字段
class Settings(BaseSettings):
    # 新配置项
    new_feature_enabled: bool = False
    new_feature_timeout: int = 60

# 2. 在 .env.example 中添加说明
# NEW_FEATURE_ENABLED=false
# NEW_FEATURE_TIMEOUT=60

# 3. 在代码中使用
from config.settings import settings

if settings.new_feature_enabled:
    # 启用新功能
    pass
```

---

## 日志记录

### ✅ 推荐做法

```python
from utils.logger import get_logger

# 获取模块级别的 logger
logger = get_logger(__name__)

# 使用不同级别的日志
logger.debug("详细的调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息", exc_info=True)  # 包含堆栈跟踪
logger.critical("严重错误", exc_info=True)

# 记录带变量的日志（使用 f-string）
logger.info(f"处理请求: {request_id}, 用户: {user_id}")

# 记录异常
try:
    risky_operation()
except Exception as e:
    logger.error(f"操作失败: {e}", exc_info=True)
```

### ❌ 不推荐做法

```python
# 不要使用 print
print("这是一条日志")
print(f"[DEBUG] 调试信息")

# 不要在每个文件中配置 logging.basicConfig
import logging
logging.basicConfig(level=logging.DEBUG)  # 会导致冲突

# 不要使用过时的字符串格式
logger.info("用户 %s 请求 %s" % (user, request))  # 使用 f-string 代替
```

### 日志级别选择

| 级别 | 使用场景 | 示例 |
|------|---------|------|
| DEBUG | 详细的调试信息 | 函数参数、中间结果 |
| INFO | 普通信息 | 请求处理、状态变化 |
| WARNING | 警告信息 | 配置缺失、降级处理 |
| ERROR | 错误信息 | 操作失败、异常捕获 |
| CRITICAL | 严重错误 | 系统崩溃、数据损坏 |

### 日志装饰器

```python
from utils.logger import log_function_call

@log_function_call()
def process_data(data: dict) -> dict:
    """处理数据"""
    return {"result": "success"}

# 自动记录:
# DEBUG: 调用 process_data({'key': 'value'})
# DEBUG: process_data 返回 {'result': 'success'}
```

### 临时调整日志级别

```python
from utils.logger import LogLevel

# 临时启用 DEBUG 级别
with LogLevel("DEBUG"):
    # 这里的代码会输出 DEBUG 日志
    logger.debug("临时调试信息")

# 这里恢复原来的级别
```

---

## 错误处理

### ✅ 推荐做法

```python
from utils.exceptions import (
    RecordNotFoundError,
    InvalidGameActionError,
    LLMTimeoutError
)

# 抛出特定的异常
def get_novel(novel_id: str):
    novel = db.query(novel_id)
    if not novel:
        raise RecordNotFoundError("Novel", novel_id)
    return novel

# 捕获并重新抛出
def process_game_action(action: str):
    try:
        result = game_engine.execute(action)
    except ValueError as e:
        raise InvalidGameActionError(action, str(e))
    return result

# FastAPI 路由中的错误处理
from fastapi import HTTPException

@app.get("/novels/{novel_id}")
async def get_novel_endpoint(novel_id: str):
    try:
        novel = get_novel(novel_id)
        return novel
    except RecordNotFoundError as e:
        # 自定义异常会被全局处理器捕获
        raise
```

### ❌ 不推荐做法

```python
# 不要使用通用异常
if not novel:
    raise Exception(f"Novel not found: {novel_id}")

# 不要吞掉异常
try:
    risky_operation()
except:  # 不要使用裸的 except
    pass

# 不要捕获过于宽泛的异常
try:
    operation()
except Exception:  # 太宽泛
    logger.error("出错了")
```

### 异常层次结构

```
AppException (所有自定义异常的基类)
├── ConfigurationError (配置相关)
├── DatabaseError (数据库相关)
├── LLMError (LLM 相关)
├── GameEngineError (游戏引擎相关)
├── WorldGenerationError (世界生成相关)
├── SaveError (存档相关)
└── AgentError (Agent 相关)
```

### 创建新的异常类

```python
# utils/exceptions.py

class NewFeatureError(AppException):
    """新功能错误"""
    pass

class SpecificError(NewFeatureError):
    """特定错误"""

    def __init__(self, detail: str):
        super().__init__(
            message=f"特定错误: {detail}",
            code="SPECIFIC_ERROR",
            details={"detail": detail}
        )
```

---

## 路径处理

### ✅ 推荐做法

```python
from config.settings import settings
from pathlib import Path

# 使用配置中的路径
db_path = settings.database_path  # Path 对象
checkpoint_db = settings.checkpoint_db_path
save_dir = settings.save_dir

# 构建相对路径
user_save = settings.save_dir / f"user_{user_id}" / "save.json"

# 确保目录存在
user_save.parent.mkdir(parents=True, exist_ok=True)

# 读写文件
with open(user_save, "w") as f:
    json.dump(data, f)
```

### ❌ 不推荐做法

```python
# 不要硬编码路径
db_path = "data/sqlite/novel.db"
checkpoint_db = "data/checkpoints/dm.db"

# 不要使用字符串拼接路径
save_path = "data/saves/" + user_id + "/save.json"  # 使用 Path 代替

# 不要忘记检查目录是否存在
with open(save_path, "w") as f:  # 可能失败
    json.dump(data, f)
```

### 路径配置清单

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `settings.project_root` | 项目根目录 | `/Users/xxx/mn_xiao_shuo` |
| `settings.data_dir` | 数据根目录 | `.../data` |
| `settings.database_path` | 数据库文件 | `.../data/sqlite/novel.db` |
| `settings.checkpoint_dir` | 检查点目录 | `.../data/checkpoints` |
| `settings.save_dir` | 存档目录 | `.../data/saves` |
| `settings.config_dir` | 配置文件目录 | `.../config` |

---

## 导入规范

### ✅ 推荐做法

```python
# 标准库导入
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict

# 第三方库导入
from fastapi import FastAPI, Depends
from pydantic import BaseModel
import yaml

# 本地模块导入（使用绝对导入）
from config.settings import settings
from utils.logger import get_logger
from utils.exceptions import RecordNotFoundError
from api.game_api import router as game_router

# 导入顺序：标准库 → 第三方库 → 本地模块
# 每组之间空一行
```

### ❌ 不推荐做法

```python
# 不要使用相对导入（在项目中）
from ..database.world_db import WorldDatabase  # 避免
from ..services.scene_refinement import SceneRefinement  # 避免

# 不要混乱的导入顺序
from api.game_api import router
import os
from fastapi import FastAPI
from utils.logger import get_logger
import sys

# 不要使用 import *
from utils.exceptions import *  # 不清楚导入了什么
```

### 导入别名规范

```python
# 常用别名
import numpy as np
import pandas as pd
from pathlib import Path

# 模块别名（避免冲突）
from api.game_api import router as game_router
from api.dm_api import router as dm_router

# 类型别名
from typing import Dict, List
GameState = Dict[str, Any]
PlayerList = List[str]
```

---

## 代码风格

### 命名规范

```python
# 类名：大驼峰命名法（PascalCase）
class GameStateManager:
    pass

class LLMBackend:
    pass

# 函数和变量：小写+下划线（snake_case）
def process_game_turn(state: GameState) -> GameState:
    player_input = get_player_input()
    game_result = execute_action(player_input)
    return game_result

# 常量：大写+下划线
MAX_SESSIONS = 100
DEFAULT_TIMEOUT = 60
API_BASE_URL = "https://api.example.com"

# 私有成员：单下划线前缀
class MyClass:
    def __init__(self):
        self._private_var = 42

    def _private_method(self):
        pass

# 环境变量：大写+下划线
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
```

### 代码格式

```python
# 使用 4 空格缩进（不使用 tab）

# 每行不超过 100 字符（推荐 88）
def long_function_name(
    parameter_one: str,
    parameter_two: int,
    parameter_three: Optional[dict] = None
) -> dict:
    """简短的文档字符串"""
    pass

# 运算符两边加空格
result = value1 + value2
is_valid = x == y and z > 0

# 逗号后面加空格
items = [1, 2, 3, 4]
params = {"a": 1, "b": 2}

# 函数定义和调用
def function(a: int, b: str) -> bool:
    return True

result = function(42, "test")
```

### 字符串格式化

```python
# ✅ 推荐：使用 f-string（Python 3.6+）
name = "Alice"
age = 30
message = f"用户 {name} 今年 {age} 岁"

# 多行 f-string
message = (
    f"用户信息:\n"
    f"  姓名: {name}\n"
    f"  年龄: {age}"
)

# ❌ 不推荐：老式格式化
message = "用户 %s 今年 %d 岁" % (name, age)
message = "用户 {} 今年 {} 岁".format(name, age)
```

---

## 类型注解

### ✅ 推荐做法

```python
from typing import Optional, List, Dict, Any, Union

# 函数参数和返回值
def process_data(
    data: dict,
    count: int,
    optional_param: Optional[str] = None
) -> List[dict]:
    """处理数据并返回结果列表"""
    return []

# 变量注解
user_id: str = "user_123"
items: List[str] = []
config: Dict[str, Any] = {}

# 类属性注解
class GameState:
    session_id: str
    turn_number: int
    players: List[str]
    metadata: Optional[Dict[str, Any]] = None

# 复杂类型
from typing import Callable, TypeVar

T = TypeVar('T')

def map_items(
    items: List[T],
    transform: Callable[[T], T]
) -> List[T]:
    return [transform(item) for item in items]
```

### 常用类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `str`, `int`, `float`, `bool` | 基础类型 | `name: str` |
| `List[T]` | 列表 | `items: List[str]` |
| `Dict[K, V]` | 字典 | `config: Dict[str, int]` |
| `Optional[T]` | 可选类型 | `value: Optional[str] = None` |
| `Union[T1, T2]` | 联合类型 | `result: Union[str, int]` |
| `Any` | 任意类型 | `data: Any`（尽量避免） |
| `Callable[[Args], Return]` | 函数类型 | `func: Callable[[int], str]` |

### Pydantic 模型

```python
from pydantic import BaseModel, Field

class GameTurnRequest(BaseModel):
    """游戏回合请求"""
    session_id: str = Field(..., description="会话 ID")
    player_input: str = Field(..., min_length=1, description="玩家输入")
    auto_save: bool = Field(True, description="是否自动保存")

    class Config:
        # 配置选项
        frozen = False  # 是否不可变
        extra = "forbid"  # 禁止额外字段
```

---

## 文档字符串

### 函数文档

```python
def calculate_score(
    events: List[dict],
    mode: str = "balanced"
) -> float:
    """
    计算事件线评分

    根据指定的模式计算事件序列的综合得分。支持三种模式：
    playability（可玩性）、narrative（叙事性）、balanced（平衡）。

    Args:
        events: 事件列表，每个事件包含类型、难度等信息
        mode: 评分模式，可选值: "playability", "narrative", "balanced"

    Returns:
        float: 综合评分，范围 0.0-1.0

    Raises:
        ValueError: 如果 mode 不是有效值
        TypeError: 如果 events 格式不正确

    Example:
        ```python
        events = [
            {"type": "combat", "difficulty": 0.7},
            {"type": "dialogue", "difficulty": 0.3}
        ]
        score = calculate_score(events, mode="balanced")
        # score = 0.65
        ```
    """
    pass
```

### 类文档

```python
class WorldGenerator:
    """
    世界生成器

    负责生成游戏世界的框架和细节，包括区域、派系、NPC 等。
    使用 LLM 进行内容生成，支持多种风格和主题。

    Attributes:
        llm_backend: LLM 后端实例
        config: 生成配置
        cache: 生成结果缓存

    Example:
        ```python
        generator = WorldGenerator(llm_backend)
        world = generator.generate(
            theme="cyberpunk",
            region_count=5
        )
        ```
    """

    def __init__(self, llm_backend: LLMBackend):
        """
        初始化世界生成器

        Args:
            llm_backend: LLM 后端实例
        """
        self.llm_backend = llm_backend
```

### 模块文档

```python
"""
游戏引擎模块

提供核心的游戏逻辑处理，包括：
- 回合处理
- 动作执行
- 状态管理
- 自动保存

Usage:
    ```python
    from game.game_engine import GameEngine

    engine = GameEngine(llm_backend)
    result = engine.process_turn(request)
    ```
"""

import os
from typing import Optional
# ...
```

---

## 快速检查清单

在提交代码前，检查以下项目：

### 配置和依赖

- [ ] 使用 `settings` 而非环境变量
- [ ] 路径使用 `Path` 对象而非字符串
- [ ] 导入使用绝对路径

### 日志和错误

- [ ] 使用 `logger` 而非 `print`
- [ ] 异常使用自定义异常类
- [ ] 错误包含足够的上下文信息

### 代码质量

- [ ] 函数和变量命名清晰
- [ ] 添加了类型注解
- [ ] 编写了文档字符串
- [ ] 遵循 PEP 8 风格

### 测试

- [ ] 手动测试过主要功能
- [ ] 考虑了边界情况
- [ ] 添加了单元测试（如适用）

---

## 工具链

### 代码格式化

```bash
# 使用 black 格式化代码
pip install black
black web/backend

# 使用 isort 排序导入
pip install isort
isort web/backend
```

### 类型检查

```bash
# 使用 mypy 检查类型
mypy web/backend
```

### 代码检查

```bash
# 使用 flake8 检查代码风格
pip install flake8
flake8 web/backend

# 使用 pylint 检查代码质量
pip install pylint
pylint web/backend
```

---

## 参考资源

- [PEP 8 - Python 代码风格指南](https://peps.python.org/pep-0008/)
- [PEP 484 - 类型注解](https://peps.python.org/pep-0484/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

---

**最后更新**: 2025-11-09
**维护者**: 开发团队
