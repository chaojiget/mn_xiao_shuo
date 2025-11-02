# 项目目录结构说明

## 目录规划原则

每个目录都有明确的职责，相关文件集中管理，便于查找和维护。

## 顶层目录结构

```
mn_xiao_shuo/
├── config/          # 配置文件（LLM、代理、小说类型）
├── data/            # 数据存储（数据库、任务、世界数据）
├── database/        # 数据库schema和迁移脚本
├── docs/            # 项目文档（按类型分类）
├── examples/        # 示例代码
├── logs/            # 日志文件
├── outputs/         # 生成的小说输出
├── scripts/         # 各类脚本（启动、开发、测试）
├── src/             # 核心业务逻辑代码
├── tests/           # 测试代码（单元测试、集成测试、端到端测试）
└── web/             # Web服务（前端+后端）
```

## 详细目录说明

### config/ - 配置文件

```
config/
├── litellm_config.yaml        # LiteLLM路由配置
├── litellm_proxy_config.yaml  # LiteLLM代理配置
├── llm_backend.yaml           # LLM后端配置
├── llm_agents.yaml            # LLM代理配置
└── novel_types.yaml           # 小说类型定义
```

**用途**：集中管理所有配置，避免硬编码

### data/ - 数据存储

```
data/
├── sqlite/          # SQLite数据库文件
├── quests/          # 任务配置YAML
└── worlds/          # 世界数据（建议新增）
```

**用途**：持久化数据存储

### database/ - 数据库管理 ⭐ 新增

```
database/
├── schema/
│   ├── core.sql              # 核心表结构
│   └── world_scaffold.sql    # 世界脚手架表
└── migrations/               # 数据库迁移脚本（未来使用）
```

**用途**：集中管理数据库schema，便于版本控制和迁移

### docs/ - 项目文档 ⭐ 重新组织

```
docs/
├── INDEX.md                  # 文档总索引
├── architecture/             # 架构设计文档
│   ├── ARCHITECTURE.md
│   ├── PROJECT_SUMMARY.md
│   └── IMPROVEMENTS_SUMMARY.md
├── guides/                   # 使用指南
│   ├── START_HERE.md
│   ├── QUICK_START.md
│   ├── OPENROUTER_SETUP.md
│   └── IMPLEMENTATION_GUIDE.md
├── features/                 # 功能文档 ⭐ 新增
│   ├── WORLD_SCAFFOLD_GUIDE.md
│   ├── QUEST_SYSTEM.md
│   ├── GAME_FEATURES.md
│   └── QUICK_START_WORLD.md
├── setup/                    # 设置和集成文档 ⭐ 新增
│   ├── SETUP_COMPLETE.md
│   ├── LITELLM_PROXY_SETUP.md
│   └── CLAUDE_AGENT_SDK_SETUP.md
├── implementation/           # 实现细节 ⭐ 新增
│   ├── WORLD_SCAFFOLD_IMPLEMENTATION.md
│   └── UI_INTEGRATION_COMPLETE.md
├── operations/              # 运维和工具 ⭐ 新增
│   ├── START_ALL_WITH_AGENT_GUIDE.md
│   ├── LITELLM_AGENT_GUIDE.md
│   └── DEMO_EXPERIENCE_GUIDE.md
├── troubleshooting/         # 故障排除 ⭐ 新增
│   ├── TROUBLESHOOTING.md
│   ├── BUG_FIXES.md
│   └── QUICK_FIX_CHECKLIST.md
├── reference/               # 参考文档 ⭐ 新增
│   ├── QUICK_REFERENCE.md
│   └── PHASE1_COMPLETE.md
└── api/                     # API文档
```

**文档分类逻辑**：
- **guides**: 如何使用（面向新用户）
- **features**: 功能说明（面向使用者）
- **setup**: 环境配置（面向部署者）
- **implementation**: 实现细节（面向开发者）
- **operations**: 运维操作（面向运维者）
- **troubleshooting**: 问题解决（面向所有人）
- **reference**: 参考信息（面向所有人）

### scripts/ - 脚本工具 ⭐ 重新组织

```
scripts/
├── init_db.py               # 数据库初始化脚本
├── start/                   # 启动脚本 ⭐ 新增
│   ├── start_all_with_agent.sh
│   ├── start_litellm_proxy.sh
│   ├── stop_all.sh
│   └── run.sh
├── dev/                     # 开发工具 ⭐ 新增
│   ├── check_services.sh
│   └── view_logs.sh
└── test/                    # 测试脚本 ⭐ 新增
    └── test_proxy_e2e.sh
```

**脚本分类逻辑**：
- **start/**: 服务启动和停止
- **dev/**: 开发辅助工具
- **test/**: 测试运行脚本

### src/ - 核心业务逻辑

```
src/
├── models/                  # 数据模型
│   ├── world_state.py
│   ├── character.py
│   ├── event_node.py
│   └── ...
├── director/                # 全局导演模块
│   ├── event_scorer.py
│   ├── clue_economy.py
│   └── consistency_auditor.py
├── llm/                     # LLM客户端
│   └── litellm_client.py
├── utils/                   # 工具函数
│   └── database.py
└── mcp_server/              # MCP服务器（计划中）
```

**用途**：可复用的核心业务逻辑，不依赖Web框架

### tests/ - 测试代码 ⭐ 重新组织

```
tests/
├── unit/                    # 单元测试 ⭐ 新增（待添加）
├── integration/             # 集成测试
│   ├── test_database.py
│   ├── test_openrouter.py
│   └── test_setup.py
└── e2e/                     # 端到端测试 ⭐ 新增
    ├── test_chat_stream.py
    ├── test_litellm_api.py
    ├── test_llm_backend.py
    └── test_world_scaffold.py
```

**测试分类逻辑**：
- **unit/**: 测试单个函数或类
- **integration/**: 测试多个模块集成
- **e2e/**: 测试完整流程

### web/ - Web服务

#### web/backend/ - 后端API ⭐ 重新组织

```
web/backend/
├── main.py                  # FastAPI入口
├── requirements.txt         # 后端依赖
├── api/                     # API路由层 ⭐ 新增
│   ├── chat_api.py
│   ├── generation_api.py
│   ├── game_api.py
│   └── world_api.py
├── services/                # 业务逻辑层 ⭐ 新增
│   ├── agent_generation.py
│   ├── world_generator.py
│   └── scene_refinement.py
├── game/                    # 游戏引擎模块
│   ├── game_engine.py
│   └── game_tools.py
├── models/                  # 数据模型 ⭐ 新增
│   └── world_models.py
├── database/                # 数据库访问层 ⭐ 新增
│   └── world_db.py
└── llm/                     # LLM集成层
```

**后端分层逻辑**：
- **api/**: FastAPI路由，处理HTTP请求/响应
- **services/**: 业务逻辑，可被多个API调用
- **game/**: 游戏引擎相关逻辑
- **models/**: 数据模型定义
- **database/**: 数据库访问封装
- **llm/**: LLM调用封装

#### web/frontend/ - 前端UI

```
web/frontend/
├── app/                     # Next.js页面
│   ├── page.tsx            # 主页
│   ├── chat/               # 聊天页面
│   ├── game/               # 游戏页面
│   └── world/              # 世界管理页面
├── components/              # React组件
│   ├── novel/              # 小说相关组件
│   ├── chat/               # 聊天相关组件
│   ├── world/              # 世界管理组件
│   └── ui/                 # shadcn/ui组件
├── hooks/                   # 自定义Hooks
├── lib/                     # 工具库
└── types/                   # TypeScript类型定义
```

## 根目录文件

```
.env                         # 环境变量（包含API密钥，不提交）
.env.example                 # 环境变量示例
.gitignore                   # Git忽略规则
README.md                    # 项目说明
CLAUDE.md                    # Claude Code指南
requirements.txt             # Python依赖
pyproject.toml               # 项目配置
uv.lock                      # UV依赖锁定
interactive_generator.py     # CLI交互式生成器
main.py                      # 命令行入口
```

## 快速导航

### 我想...

**启动服务**
- 一键启动：`./scripts/start/start_all_with_agent.sh`
- 单独启动后端：`cd web/backend && uvicorn main:app --reload`
- 单独启动前端：`cd web/frontend && npm run dev`

**查看文档**
- 快速开始：`docs/guides/QUICK_START.md`
- 功能列表：`docs/features/`
- 故障排除：`docs/troubleshooting/TROUBLESHOOTING.md`

**运行测试**
- 集成测试：`python tests/integration/test_setup.py`
- 端到端测试：`python tests/e2e/test_litellm_api.py`

**修改配置**
- LLM配置：`config/litellm_config.yaml`
- 环境变量：`.env`

**查看数据**
- 数据库：`data/sqlite/novel.db`
- 日志：`logs/`
- 输出：`outputs/`

## 迁移说明

如果你是从旧的目录结构迁移过来，请参考：

- **迁移计划**：`docs/DIRECTORY_REORGANIZATION_PLAN.md`
- **迁移指南**：`docs/DIRECTORY_MIGRATION_GUIDE.md`
- **迁移脚本**：`scripts/migrate_directory_structure.sh`

## 最佳实践

### 添加新功能时

1. **代码**：在 `src/` 或 `web/backend/` 的对应子目录添加
2. **测试**：在 `tests/` 的对应子目录添加测试
3. **文档**：在 `docs/features/` 添加功能说明
4. **配置**：如需新配置，添加到 `config/`

### 添加新文档时

根据文档类型选择合适的子目录：
- 使用指南 → `docs/guides/`
- 功能说明 → `docs/features/`
- 设置步骤 → `docs/setup/`
- 实现细节 → `docs/implementation/`
- 运维操作 → `docs/operations/`
- 问题解决 → `docs/troubleshooting/`
- 参考信息 → `docs/reference/`

### 添加新脚本时

根据脚本用途选择合适的子目录：
- 启动/停止服务 → `scripts/start/`
- 开发辅助工具 → `scripts/dev/`
- 测试运行脚本 → `scripts/test/`
- 数据库操作 → `scripts/` 根目录

## 目录结构的优势

✅ **清晰的职责划分**：每个目录有明确的用途
✅ **便于查找**：根据类型快速定位文件
✅ **易于维护**：相关文件集中管理
✅ **降低认知负担**：新开发者能快速理解项目结构
✅ **符合最佳实践**：遵循Python和Web项目规范
✅ **便于扩展**：新功能有明确的归属位置

## 相关文档

- 完整规划：`docs/DIRECTORY_REORGANIZATION_PLAN.md`
- 迁移指南：`docs/DIRECTORY_MIGRATION_GUIDE.md`
- 项目架构：`docs/architecture/ARCHITECTURE.md`
