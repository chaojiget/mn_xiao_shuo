# 目录迁移执行指南

## 概述

本指南将引导你完成项目目录结构的重组。整个过程分为两个阶段：

1. **自动迁移阶段**：运行脚本自动移动文件
2. **手动修复阶段**：更新导入路径和引用

## 前置条件

### 1. 提交当前更改

在开始迁移前，请确保所有当前更改已提交：

```bash
git status
git add .
git commit -m "chore: save work before directory reorganization"
```

### 2. 创建新分支

建议在新分支上进行迁移：

```bash
git checkout -b refactor/directory-reorganization
```

### 3. 备份数据库

如果有重要数据，请先备份：

```bash
cp -r data/sqlite data/sqlite.backup
```

## 阶段一：自动迁移（5分钟）

### 步骤1：运行迁移脚本

```bash
# 从项目根目录运行
./scripts/migrate_directory_structure.sh
```

脚本将自动完成：
- ✅ 移动数据库schema文件到 `database/schema/`
- ✅ 重组docs目录（分类到features/setup/implementation等）
- ✅ 重组scripts目录（分类到start/dev/test）
- ✅ 重组tests目录（分类到e2e/unit）
- ✅ 重组web/backend目录（分类到api/services/models等）
- ✅ 创建必要的`__init__.py`文件

### 步骤2：验证文件移动

```bash
# 检查git状态
git status

# 应该看到大量文件被重命名
# 确认没有文件被意外删除
```

## 阶段二：手动修复（30-60分钟）

### 步骤1：更新 web/backend/main.py

当前文件：`web/backend/main.py`

需要更新的导入：

```python
# 原导入（假设存在）
from chat_api import router as chat_router
from generation_api import router as generation_router
from game_api import router as game_router
from world_api import router as world_router
from world_db import WorldDB
from world_models import WorldFramework

# 新导入
from api.chat_api import router as chat_router
from api.generation_api import router as generation_router
from api.game_api import router as game_router
from api.world_api import router as world_router
from database.world_db import WorldDB
from models.world_models import WorldFramework
```

### 步骤2：更新 API 文件导入

需要更新的文件：
- `web/backend/api/chat_api.py`
- `web/backend/api/generation_api.py`
- `web/backend/api/game_api.py`
- `web/backend/api/world_api.py`

示例（以 `game_api.py` 为例）：

```python
# 原导入
from game_engine import GameEngine
from world_db import WorldDB

# 新导入
from ..game.game_engine import GameEngine
from ..database.world_db import WorldDB
```

### 步骤3：更新服务文件导入

需要更新的文件：
- `web/backend/services/agent_generation.py`
- `web/backend/services/world_generator.py`
- `web/backend/services/scene_refinement.py`

示例（以 `world_generator.py` 为例）：

```python
# 原导入
from world_models import WorldFramework, Region, Faction
from world_db import WorldDB

# 新导入
from ..models.world_models import WorldFramework, Region, Faction
from ..database.world_db import WorldDB
```

### 步骤4：更新游戏引擎导入

需要更新的文件：
- `web/backend/game/game_engine.py`
- `web/backend/game/game_tools.py`

示例（以 `game_engine.py` 为例）：

```python
# 原导入
from world_db import WorldDB
from world_models import Scene

# 新导入
from ..database.world_db import WorldDB
from ..models.world_models import Scene
```

### 步骤5：更新启动脚本路径

#### 5.1 更新 `scripts/start/start_all_with_agent.sh`

```bash
# 原路径
PROJECT_ROOT="$(dirname "$0")"
LOG_DIR="logs"

# 新路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
```

#### 5.2 更新 `scripts/start/start_litellm_proxy.sh`

```bash
# 更新配置文件路径
CONFIG_PATH="$PROJECT_ROOT/config/litellm_proxy_config.yaml"
```

#### 5.3 更新 `scripts/dev/check_services.sh`

```bash
# 更新根目录引用
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
```

### 步骤6：更新数据库初始化脚本

文件：`scripts/init_db.py`

```python
# 原路径
schema_path = "schema.sql"
world_schema_path = "schema_world_scaffold.sql"

# 新路径
schema_path = "database/schema/core.sql"
world_schema_path = "database/schema/world_scaffold.sql"
```

### 步骤7：更新测试文件导入

需要更新的文件：
- `tests/integration/test_database.py`
- `tests/integration/test_setup.py`
- `tests/e2e/test_chat_stream.py`
- `tests/e2e/test_litellm_api.py`
- `tests/e2e/test_llm_backend.py`
- `tests/e2e/test_world_scaffold.py`

确保所有导入使用绝对路径（从项目根目录）：

```python
# 推荐：使用sys.path添加项目根目录
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 然后使用绝对导入
from src.llm.litellm_client import LiteLLMClient
from web.backend.database.world_db import WorldDB
```

## 阶段三：测试验证（15分钟）

### 步骤1：测试后端启动

```bash
# 启动后端
cd web/backend
source ../../.venv/bin/activate
python -m uvicorn main:app --reload --port 8000
```

检查控制台输出，确保没有导入错误。

### 步骤2：测试前端启动

```bash
# 在新终端中
cd web/frontend
npm run dev
```

访问 http://localhost:3000 确认页面正常。

### 步骤3：运行集成测试

```bash
# 从项目根目录
source .venv/bin/activate

# 运行数据库测试
python tests/integration/test_database.py

# 运行设置测试
python tests/integration/test_setup.py
```

### 步骤4：运行端到端测试

```bash
# 测试LiteLLM API
python tests/e2e/test_litellm_api.py

# 测试世界脚手架
python tests/e2e/test_world_scaffold.py
```

### 步骤5：测试启动脚本

```bash
# 测试完整启动流程
./scripts/start/start_all_with_agent.sh

# 检查所有服务是否正常启动
./scripts/dev/check_services.sh

# 查看日志
./scripts/dev/view_logs.sh
```

## 阶段四：文档更新（15分钟）

### 步骤1：更新 README.md

更新所有文件路径引用，例如：

```markdown
# 原路径
运行 `./start_all_with_agent.sh` 启动所有服务

# 新路径
运行 `./scripts/start/start_all_with_agent.sh` 启动所有服务
```

### 步骤2：更新 CLAUDE.md

更新关键命令和路径引用。

### 步骤3：更新 docs/INDEX.md

更新文档索引，反映新的目录结构：

```markdown
## 文档结构

### 快速开始
- [开始这里](guides/START_HERE.md)
- [快速启动](guides/QUICK_START.md)

### 功能文档
- [世界脚手架指南](features/WORLD_SCAFFOLD_GUIDE.md)
- [任务系统](features/QUEST_SYSTEM.md)
- [游戏功能](features/GAME_FEATURES.md)

### 设置指南
- [LiteLLM代理设置](setup/LITELLM_PROXY_SETUP.md)
- [Claude Agent SDK设置](setup/CLAUDE_AGENT_SDK_SETUP.md)

### 故障排除
- [常见问题](troubleshooting/TROUBLESHOOTING.md)
- [Bug修复日志](troubleshooting/BUG_FIXES.md)
```

## 阶段五：提交更改（5分钟）

### 步骤1：检查更改

```bash
git status
git diff --cached
```

### 步骤2：分批提交

```bash
# 提交文件移动
git add -A
git commit -m "refactor: reorganize directory structure

- Move database schemas to database/schema/
- Categorize docs into features/setup/implementation/operations/troubleshooting/reference
- Reorganize scripts into start/dev/test
- Categorize tests into e2e/unit
- Restructure web/backend into api/services/models/database
"

# 提交导入路径更新
git add web/backend/
git commit -m "refactor: update import paths in web/backend"

# 提交脚本更新
git add scripts/
git commit -m "refactor: update paths in scripts"

# 提交测试更新
git add tests/
git commit -m "refactor: update import paths in tests"

# 提交文档更新
git add *.md docs/
git commit -m "docs: update documentation for new directory structure"
```

### 步骤3：合并到主分支

```bash
# 切换回主分支
git checkout main

# 合并重构分支
git merge refactor/directory-reorganization

# 推送到远程（如果有）
git push origin main
```

## 常见问题

### Q1: 导入错误：ModuleNotFoundError

**症状**：运行时报错 `ModuleNotFoundError: No module named 'xxx'`

**解决**：
1. 检查是否所有目录都有 `__init__.py` 文件
2. 确认导入路径使用相对导入（`..module`）或绝对导入
3. 检查 `PYTHONPATH` 是否包含项目根目录

### Q2: 脚本找不到文件

**症状**：脚本报错 `No such file or directory`

**解决**：
1. 确保脚本中使用绝对路径而非相对路径
2. 使用 `PROJECT_ROOT` 变量来构建路径
3. 检查 `$(dirname "${BASH_SOURCE[0]}")` 是否正确

### Q3: 测试失败

**症状**：测试报错或无法找到模块

**解决**：
1. 确保在项目根目录运行测试
2. 检查测试文件中的导入路径
3. 确认虚拟环境已激活

### Q4: 前端无法连接后端

**症状**：前端API调用失败

**解决**：
1. 检查后端是否正常启动（端口8000）
2. 检查前端API配置（应该还是 `http://localhost:8000`）
3. 查看后端日志确认错误信息

## 回滚方案

如果迁移失败，可以使用以下命令回滚：

```bash
# 方案1：Git回滚
git reset --hard HEAD~N  # N是提交次数

# 方案2：恢复到迁移前的提交
git log  # 找到迁移前的commit hash
git reset --hard <commit-hash>

# 方案3：删除分支重新开始
git checkout main
git branch -D refactor/directory-reorganization
```

## 验收检查清单

完成以下检查确认迁移成功：

- [ ] 所有文件已移动到新位置
- [ ] 没有文件丢失或重复
- [ ] 后端可以正常启动
- [ ] 前端可以正常启动
- [ ] 所有集成测试通过
- [ ] 所有端到端测试通过
- [ ] 启动脚本可以正常运行
- [ ] 开发工具脚本可以正常运行
- [ ] 文档路径引用已更新
- [ ] README.md已更新
- [ ] CLAUDE.md已更新
- [ ] docs/INDEX.md已更新
- [ ] Git提交历史清晰
- [ ] 所有更改已推送到远程（如果需要）

## 预计时间

- 阶段一（自动迁移）：5分钟
- 阶段二（手动修复）：30-60分钟
- 阶段三（测试验证）：15分钟
- 阶段四（文档更新）：15分钟
- 阶段五（提交更改）：5分钟

**总计**：约1-2小时

## 下一步

迁移完成后，你可以：

1. 阅读 `docs/DIRECTORY_REORGANIZATION_PLAN.md` 了解新的目录结构设计理念
2. 更新团队文档，通知其他开发者目录结构变更
3. 继续开发新功能，享受更清晰的项目结构！
