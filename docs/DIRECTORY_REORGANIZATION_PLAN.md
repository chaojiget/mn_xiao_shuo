# 目录重组规划方案

## 当前问题分析

### 根目录问题
- 散落大量测试文件：`test_*.py`（6个文件）
- 多个启动脚本混乱：`start_*.sh`, `stop_all.sh`, `run.sh`等
- 重复的schema文件：`schema.sql`, `schema_world_scaffold.sql`
- 工具脚本未分类：`check_services.sh`, `view_logs.sh`

### docs目录问题
- 文档缺乏明确分类，平铺在根目录下（30+个文件）
- 设置指南、实现文档、问题修复文档混在一起
- 缺少清晰的文档索引和导航

### web/backend目录问题
- API、模型、工具类文件混在一起
- game相关文件（game_api.py, game_engine.py, game_tools.py）未归类
- world相关文件（world_api.py, world_db.py, world_generator.py, world_models.py）未归类
- llm目录已存在但其他文件未整理

### src目录问题
- 结构相对清晰，但缺少一些模块

## 目标目录结构

```
mn_xiao_shuo/
├── .venv/                    # 虚拟环境
├── .git/                     # Git仓库
├── config/                   # ✅ 配置文件（已存在）
│   ├── litellm_config.yaml
│   ├── litellm_proxy_config.yaml
│   ├── llm_backend.yaml
│   ├── llm_agents.yaml
│   └── novel_types.yaml
├── data/                     # ✅ 数据目录（已存在）
│   ├── sqlite/              # 数据库文件
│   ├── quests/              # 任务配置
│   └── worlds/              # 世界数据（建议新增）
├── database/                 # 📦 新增：数据库schema和迁移
│   ├── schema/
│   │   ├── core.sql         # 核心表结构（原schema.sql）
│   │   └── world_scaffold.sql  # 世界脚手架表（原schema_world_scaffold.sql）
│   └── migrations/          # 数据库迁移脚本
├── docs/                     # 📖 文档目录（重新组织）
│   ├── INDEX.md             # ✅ 总索引（已存在）
│   ├── architecture/        # ✅ 架构设计（已存在）
│   │   ├── ARCHITECTURE.md
│   │   ├── PROJECT_SUMMARY.md
│   │   └── IMPROVEMENTS_SUMMARY.md
│   ├── guides/              # ✅ 使用指南（已存在，需补充）
│   │   ├── START_HERE.md
│   │   ├── QUICK_START.md
│   │   ├── OPENROUTER_SETUP.md
│   │   ├── IMPLEMENTATION_GUIDE.md
│   │   └── AGENT_SDK_WITH_DEEPSEEK.md
│   ├── features/            # 📦 新增：功能文档
│   │   ├── WORLD_SCAFFOLD_GUIDE.md     # 从根目录移动
│   │   ├── QUEST_SYSTEM.md             # 从根目录移动
│   │   ├── GAME_FEATURES.md            # 从根目录移动
│   │   └── QUICK_START_WORLD.md        # 从根目录移动
│   ├── setup/               # 📦 新增：设置和集成文档
│   │   ├── SETUP_COMPLETE.md
│   │   ├── LITELLM_PROXY_SETUP.md
│   │   ├── CLAUDE_AGENT_SDK_SETUP.md
│   │   ├── LLM_BACKEND_INTEGRATION.md
│   │   └── WORLD_SYSTEM_INTEGRATION_COMPLETE.md
│   ├── implementation/      # 📦 新增：实现细节
│   │   ├── WORLD_SCAFFOLD_IMPLEMENTATION.md
│   │   ├── CLAUDE_AGENT_SDK_IMPLEMENTATION.md
│   │   ├── LLM_BACKEND_INTEGRATION_COMPLETE.md
│   │   └── UI_INTEGRATION_COMPLETE.md
│   ├── operations/          # 📦 新增：运维和工具
│   │   ├── START_ALL_WITH_AGENT_GUIDE.md
│   │   ├── LITELLM_AGENT_GUIDE.md
│   │   ├── LLM_BACKEND_GUIDE.md
│   │   └── DEMO_EXPERIENCE_GUIDE.md
│   ├── troubleshooting/     # 📦 新增：故障排除
│   │   ├── TROUBLESHOOTING.md
│   │   ├── BUG_FIXES.md
│   │   ├── BUG_FIX_502_GATEWAY.md
│   │   └── QUICK_FIX_CHECKLIST.md
│   ├── reference/           # 📦 新增：参考文档
│   │   ├── QUICK_REFERENCE.md
│   │   ├── IMPLEMENTATION_GAP_ANALYSIS.md
│   │   └── PHASE1_COMPLETE.md
│   └── api/                 # ✅ API文档（已存在）
├── scripts/                  # 🔧 脚本目录（重新组织）
│   ├── init_db.py           # ✅ 已存在
│   ├── start/               # 📦 新增：启动脚本
│   │   ├── start_all_with_agent.sh  # 从根目录移动
│   │   ├── start_litellm_proxy.sh   # 从根目录移动
│   │   └── stop_all.sh              # 从根目录移动
│   ├── dev/                 # 📦 新增：开发工具
│   │   ├── check_services.sh        # 从根目录移动
│   │   └── view_logs.sh             # 从根目录移动
│   └── test/                # 📦 新增：测试脚本
│       └── test_proxy_e2e.sh        # 从根目录移动
├── src/                      # 🏗️ 源代码（核心业务逻辑）
│   ├── models/              # ✅ 数据模型（已存在）
│   ├── director/            # ✅ 全局导演（已存在）
│   ├── llm/                 # ✅ LLM客户端（已存在）
│   ├── utils/               # ✅ 工具函数（已存在）
│   └── mcp_server/          # ✅ MCP服务器（已存在）
├── tests/                    # 🧪 测试目录（重新组织）
│   ├── unit/                # 📦 新增：单元测试
│   ├── integration/         # ✅ 集成测试（已存在）
│   │   ├── test_database.py
│   │   ├── test_openrouter.py
│   │   └── test_setup.py
│   └── e2e/                 # 📦 新增：端到端测试
│       ├── test_chat_stream.py      # 从根目录移动
│       ├── test_litellm_api.py      # 从根目录移动
│       ├── test_llm_backend.py      # 从根目录移动
│       └── test_world_scaffold.py   # 从根目录移动
├── web/                      # 🌐 Web服务
│   ├── backend/             # 后端（重新组织）
│   │   ├── api/             # 📦 API路由层
│   │   │   ├── chat_api.py          # 从上层移动
│   │   │   ├── generation_api.py    # 从上层移动
│   │   │   ├── game_api.py          # 从上层移动
│   │   │   └── world_api.py         # 从上层移动
│   │   ├── services/        # 📦 业务逻辑层
│   │   │   ├── agent_generation.py  # 从上层移动
│   │   │   ├── world_generator.py   # 从上层移动
│   │   │   └── scene_refinement.py  # 从上层移动
│   │   ├── game/            # ✅ 游戏引擎（已存在）
│   │   │   ├── game_engine.py       # 从上层移动
│   │   │   └── game_tools.py        # 从上层移动
│   │   ├── models/          # 📦 新增：数据模型
│   │   │   └── world_models.py      # 从上层移动
│   │   ├── database/        # 📦 新增：数据库访问
│   │   │   └── world_db.py          # 从上层移动
│   │   ├── llm/             # ✅ LLM集成（已存在）
│   │   ├── main.py          # ✅ FastAPI入口（保持）
│   │   └── requirements.txt # ✅ 后端依赖（保持）
│   └── frontend/            # ✅ 前端（已存在，结构良好）
├── logs/                     # ✅ 日志目录（已存在）
├── outputs/                  # ✅ 输出目录（已存在）
├── examples/                 # ✅ 示例代码（已存在）
├── .env                      # ✅ 环境变量
├── .env.example              # ✅ 环境变量示例
├── .gitignore                # ✅ Git忽略规则
├── README.md                 # ✅ 项目说明
├── CLAUDE.md                 # ✅ Claude指南
├── requirements.txt          # ✅ Python依赖
├── pyproject.toml            # ✅ 项目配置
├── interactive_generator.py  # ✅ CLI交互生成器（保留在根目录）
└── main.py                   # ✅ 主入口（保留在根目录）
```

## 重组步骤

### 第一步：创建新目录

```bash
# 数据库schema目录
mkdir -p database/schema
mkdir -p database/migrations

# 文档重组目录
mkdir -p docs/features
mkdir -p docs/setup
mkdir -p docs/implementation
mkdir -p docs/operations
mkdir -p docs/troubleshooting
mkdir -p docs/reference

# 脚本重组目录
mkdir -p scripts/start
mkdir -p scripts/dev
mkdir -p scripts/test

# 测试重组目录
mkdir -p tests/unit
mkdir -p tests/e2e

# web/backend重组目录
mkdir -p web/backend/api
mkdir -p web/backend/services
mkdir -p web/backend/models
mkdir -p web/backend/database
```

### 第二步：移动数据库schema文件

```bash
# 移动schema文件
mv schema.sql database/schema/core.sql
mv schema_world_scaffold.sql database/schema/world_scaffold.sql
```

### 第三步：重组docs目录

```bash
# 移动功能文档
mv docs/WORLD_SCAFFOLD_GUIDE.md docs/features/
mv docs/QUEST_SYSTEM.md docs/features/
mv docs/GAME_FEATURES.md docs/features/
mv docs/QUICK_START_WORLD.md docs/features/

# 移动设置文档
mv docs/SETUP_COMPLETE.md docs/setup/
mv docs/LITELLM_PROXY_SETUP.md docs/setup/
mv docs/CLAUDE_AGENT_SDK_SETUP.md docs/setup/
mv docs/LLM_BACKEND_INTEGRATION.md docs/setup/
mv docs/WORLD_SYSTEM_INTEGRATION_COMPLETE.md docs/setup/
mv docs/LITELLM_PROXY_MIGRATION_COMPLETE.md docs/setup/

# 移动实现文档
mv docs/WORLD_SCAFFOLD_IMPLEMENTATION.md docs/implementation/
mv docs/CLAUDE_AGENT_SDK_IMPLEMENTATION.md docs/implementation/
mv docs/LLM_BACKEND_INTEGRATION_COMPLETE.md docs/implementation/
mv docs/UI_INTEGRATION_COMPLETE.md docs/implementation/
mv docs/IMPLEMENTATION_SUMMARY.md docs/implementation/

# 移动运维文档
mv docs/START_ALL_WITH_AGENT_GUIDE.md docs/operations/
mv docs/LITELLM_AGENT_GUIDE.md docs/operations/
mv docs/LLM_BACKEND_GUIDE.md docs/operations/
mv docs/LLM_BACKEND_USAGE.md docs/operations/
mv docs/DEMO_EXPERIENCE_GUIDE.md docs/operations/

# 移动故障排除文档
mv docs/TROUBLESHOOTING.md docs/troubleshooting/
mv docs/BUG_FIXES.md docs/troubleshooting/
mv docs/BUG_FIX_502_GATEWAY.md docs/troubleshooting/
mv docs/QUICK_FIX_CHECKLIST.md docs/troubleshooting/

# 移动参考文档
mv docs/QUICK_REFERENCE.md docs/reference/
mv docs/IMPLEMENTATION_GAP_ANALYSIS.md docs/reference/
mv docs/PHASE1_COMPLETE.md docs/reference/
mv docs/CLAUDE_AGENT_SDK_EVALUATION.md docs/reference/
```

### 第四步：重组scripts目录

```bash
# 移动启动脚本
mv start_all_with_agent.sh scripts/start/
mv start_litellm_proxy.sh scripts/start/
mv stop_all.sh scripts/start/
mv run.sh scripts/start/

# 移动开发工具脚本
mv check_services.sh scripts/dev/
mv view_logs.sh scripts/dev/

# 移动测试脚本
mv test_proxy_e2e.sh scripts/test/
```

### 第五步：重组tests目录

```bash
# 移动端到端测试
mv test_chat_stream.py tests/e2e/
mv test_litellm_api.py tests/e2e/
mv test_llm_backend.py tests/e2e/
mv test_world_scaffold.py tests/e2e/
```

### 第六步：重组web/backend目录

```bash
cd web/backend

# 移动API文件
mv chat_api.py api/
mv generation_api.py api/
mv game_api.py api/
mv world_api.py api/

# 移动服务文件
mv agent_generation.py services/
mv world_generator.py services/
mv scene_refinement.py services/

# 移动游戏引擎文件
mv game_engine.py game/
mv game_tools.py game/

# 移动模型文件
mv world_models.py models/

# 移动数据库文件
mv world_db.py database/
```

### 第七步：更新导入路径

需要更新以下文件中的导入路径：

1. `web/backend/main.py` - 更新所有API、服务、模型的导入
2. 所有移动后的API文件 - 更新相对导入
3. 所有服务文件 - 更新模型和数据库导入
4. 测试文件 - 更新导入路径

### 第八步：更新脚本路径引用

需要更新的脚本：
- `scripts/start/start_all_with_agent.sh` - 更新日志路径等
- `scripts/dev/check_services.sh` - 更新配置文件路径
- 所有文档中引用的脚本路径

## 需要更新的关键文件

### 1. web/backend/main.py

```python
# 原导入
from chat_api import router as chat_router
from generation_api import router as generation_router
from game_api import router as game_router
from world_api import router as world_router

# 新导入
from api.chat_api import router as chat_router
from api.generation_api import router as generation_router
from api.game_api import router as game_router
from api.world_api import router as world_router
```

### 2. API文件中的导入

```python
# 例如 web/backend/api/game_api.py
# 原导入
from game_engine import GameEngine
from world_db import WorldDB

# 新导入
from ..game.game_engine import GameEngine
from ..database.world_db import WorldDB
```

### 3. 启动脚本

```bash
# scripts/start/start_all_with_agent.sh
# 更新路径为相对于项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
```

## 迁移检查清单

- [ ] 创建所有新目录
- [ ] 移动database schema文件
- [ ] 重组docs目录文件
- [ ] 移动scripts脚本文件
- [ ] 移动tests测试文件
- [ ] 重组web/backend文件
- [ ] 更新web/backend/main.py导入
- [ ] 更新所有API文件导入
- [ ] 更新所有服务文件导入
- [ ] 更新所有测试文件导入
- [ ] 更新scripts中的路径引用
- [ ] 更新README.md中的路径引用
- [ ] 更新CLAUDE.md中的路径引用
- [ ] 更新docs/INDEX.md文档索引
- [ ] 运行测试验证迁移
- [ ] 验证所有脚本可正常运行

## 预期效果

1. **清晰的目录结构**: 每个目录有明确的职责
2. **更好的可维护性**: 相关文件集中管理
3. **降低认知负担**: 新开发者能快速找到需要的文件
4. **规范的项目组织**: 符合Python和Web项目最佳实践
5. **便于扩展**: 新功能有明确的归属位置

## 风险和注意事项

1. **导入路径变更**: 必须仔细更新所有导入语句
2. **脚本路径引用**: shell脚本中的相对路径需要调整
3. **Git历史**: 使用`git mv`保留文件历史
4. **测试验证**: 移动后必须运行完整测试套件
5. **文档同步**: 所有文档中的路径引用需要更新
6. **渐进式迁移**: 建议分批次进行，每次迁移后验证

## 实施建议

1. **创建新分支**: `git checkout -b refactor/directory-reorganization`
2. **分阶段执行**: 每完成一个步骤提交一次
3. **持续测试**: 每个阶段后运行测试
4. **文档先行**: 先更新文档结构，后移动代码
5. **保留备份**: 在`.gitignore`外保留一份完整备份
