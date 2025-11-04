# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# 核心工作原则

## ⚠️ 最高优先级原则
**严格遵循已有的技术规划和文档，不要擅自改变技术栈或架构决策**

- ✅ 实施前必须仔细阅读相关文档（如 `docs/TECHNICAL_IMPLEMENTATION_PLAN.md`）
- ✅ 如果文档明确规定使用某个技术栈，必须严格遵循
- ✅ 如果需要偏离规划，必须先征得用户同意，说明原因
- ❌ 不要因为"更简单"、"更熟悉"等理由擅自更换技术方案
- ❌ 不要在未经许可的情况下修改核心架构设计

## 其他重要原则
- 使用中文和我交流
- 注意文档目录的规划/管理
- 直面问题，解决问题，不要试图绕过去，顺藤摸瓜找到问题

## 项目概述

这是一个基于 AI 驱动的长篇小说生成系统,支持科幻和玄幻/仙侠两大类型。系统采用"全局导演"(Global Director)架构,通过事件线评分、一致性审计和线索经济管理来生成连贯的长篇小说。

**最新更新(2025-11-03)**: 完成 Phase 2 游戏工具系统（基于 Claude Agent SDK）

**Phase 2 实施（2025-11-03）**:
- ✅ 使用 Claude Agent SDK + MCP Server 架构
- ✅ 11个游戏工具（@tool 装饰器）
  - 7个核心工具（状态查询、物品、HP、检定、位置、存档）
  - 5个任务工具（创建、查询、激活、更新进度、完成）
- ✅ DM Agent 实现（ClaudeAgentOptions + query）
- ✅ 游戏状态管理器（数据库 + 缓存）
- ✅ 存档系统（SaveService + 3个表 + 6个API端点）
- ✅ 任务系统（Quest 数据模型 + 5个MCP工具）
- ✅ 完整的测试覆盖（单元测试 18/18 通过）
- 📖 详见: `docs/TECHNICAL_IMPLEMENTATION_PLAN.md`、`docs/implementation/CLAUDE_AGENT_SDK_IMPLEMENTATION.md`、`docs/implementation/PHASE2_SAVE_SYSTEM_IMPLEMENTATION.md`、`docs/implementation/PHASE2_QUEST_SYSTEM_IMPLEMENTATION.md`

**目录重组（2025-11-02）**:

**目录重组（最新）**:
- ✅ 文档分类管理（features/setup/implementation/operations/troubleshooting/reference）
- ✅ 脚本分类管理（start/dev/test）
- ✅ 测试分类管理（integration/e2e/unit）
- ✅ 后端分层架构（api/services/models/database/game）
- ✅ 数据库schema集中管理（database/schema/）
- 📖 详见: `docs/DIRECTORY_STRUCTURE.md` 和 `docs/MIGRATION_COMPLETE.md`

**世界脚手架系统**:
- ✅ 世界框架生成（主题、风格圣经、区域、派系）
- ✅ 场景细化流水线（结构→感官→可供性→镜头，4个Pass）
- ✅ 可供性chips交互（解决"不知道做什么"）
- ✅ Canon固化机制（保证世界一致性）
- ✅ 世界管理页面（Web UI，树状导航）
- 📖 详见: `docs/features/WORLD_SCAFFOLD_GUIDE.md` 和 `docs/features/QUICK_START_WORLD.md`

**全局导演架构**:
- ✅ 可编辑设定系统(支持动态修改世界观、主角、路线)
- ✅ NPC按需生成机制(seed→instantiate→engage→adapt→retire)
- ✅ 事件线评分系统(可玩性/叙事/混合三种模式)
- ✅ 线索经济管理(伏笔SLA、证据链验证、健康度监控)
- ✅ 一致性审计系统(硬规则/因果/资源/角色/时间线检查)
- ✅ 会话历史管理(完整记录、支持分支、智能上下文)
- 📖 详见: `docs/architecture/IMPROVEMENTS_SUMMARY.md` 和 `docs/reference/QUICK_REFERENCE.md`

## 关键命令

### Python 环境管理

**本项目使用 `uv` 作为 Python 包管理器**

`uv` 是一个超快的 Python 包管理器，比 pip 快 10-100 倍。

```bash
# 安装 uv (如果未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 使用 uv 安装依赖
uv pip install -r requirements.txt

# 使用 uv 运行 Python 命令
uv run python script.py

# 使用 uv 运行后端服务
cd web/backend
uv run uvicorn main:app --reload --port 8000

# 查看已安装的包
uv pip list

# 安装单个包
uv pip install package-name
```

**注意：**
- 不要使用 `pip` 或 `python` 命令，统一使用 `uv pip` 和 `uv run python`
- `uv` 会自动管理虚拟环境，无需手动激活 `.venv`
- 如果遇到包未找到的错误，使用 `uv pip install` 安装

### 开发环境设置

```bash
# 安装后端依赖 (使用 uv)
uv pip install -r requirements.txt

# 安装前端依赖 (首次运行)
cd web/frontend && npm install && cd ../..

# 初始化数据库
uv run python scripts/init_db.py
```

### 运行服务

```bash
# 一键启动完整系统 (LiteLLM Proxy + 后端 + 前端)
./scripts/start/start_all_with_agent.sh

# 停止所有服务
./scripts/start/stop_all.sh

# 或手动启动后端 (端口 8000) - 使用 uv
cd web/backend
uv run uvicorn main:app --reload --port 8000

# 或手动启动前端 (端口 3000)
cd web/frontend
npm run dev

# CLI 交互式生成 - 使用 uv
uv run python interactive_generator.py
```

### 测试

```bash
# 测试数据库连接 - 使用 uv
uv run python tests/integration/test_database.py

# 测试 OpenRouter API - 使用 uv
uv run python tests/integration/test_openrouter.py

# 测试完整设置 - 使用 uv
uv run python tests/integration/test_setup.py

# 端到端测试 - 使用 uv
uv run python tests/e2e/test_litellm_api.py
uv run python tests/e2e/test_world_scaffold.py
```

### 开发工具

```bash
# 检查服务状态
./scripts/dev/check_services.sh

# 查看日志
./scripts/dev/view_logs.sh
```

### 前端开发

```bash
cd web/frontend

# 开发模式
npm run dev

# 生产构建
npm run build

# 启动生产服务器
npm start

# 代码检查
npm run lint
```

## 核心架构

### 1. 三层架构

```
┌──────────────────────────────────────────┐
│  用户界面层                               │
│  - Web UI (Next.js + shadcn/ui)         │
│  - CLI (interactive_generator.py)       │
└─────────────┬────────────────────────────┘
              │
┌─────────────▼────────────────────────────┐
│  业务逻辑层                               │
│  - FastAPI Backend (web/backend/main.py)│
│  - Global Director (未完全实现)          │
└─────────────┬────────────────────────────┘
              │
┌─────────────▼────────────────────────────┐
│  数据与 AI 层                             │
│  - SQLite Database (schema.sql)         │
│  - LiteLLM Router (OpenRouter)          │
│  - DeepSeek V3 Model                    │
└──────────────────────────────────────────┘
```

### 2. 数据模型层次 (src/models/)

**核心状态管理:**
- `WorldState`: 世界状态快照,包含 locations, characters, factions, resources
- `Character`: 角色状态,包含 attributes, resources, inventory, relationships
- `Location`, `Faction`, `Resource`: 辅助状态对象

**事件系统:**
- `EventNode`: 事件节点,包含 prerequisites, effects, scoring metrics
- `EventArc`: 事件线,管理多个相关事件

**执行控制:**
- `ActionQueue`: 动作队列,定义 scene/interaction/check/tool/outcome 步骤
- `Hint`: 提示系统 (implicit/explicit/red_herring)

**线索经济:**
- `Clue`, `Evidence`: 线索与证据管理
- `Setup`: 伏笔/铺垫,带 SLA 截止时间
- `ClueRegistry`: 线索登记册,跟踪发现与验证状态

### 3. LLM 集成架构

**配置路径:** `config/litellm_config.yaml`

**模型选择策略:**
- **DeepSeek V3** (`deepseek`): 默认模型,高性价比,中文友好,用于所有章节生成
- Claude Sonnet (`claude-sonnet`): 高质量备用模型
- Claude Haiku (`claude-haiku`): 快速简单任务
- GPT-4 (`gpt-4`): 备用模型
- Qwen 2.5 (`qwen`): 中文优化备用

**LiteLLM 客户端:**
- 位置: `src/llm/litellm_client.py`
- 初始化时必须传入 `config_path` 参数(使用绝对路径)
- 方法:
  - `generate()`: 基础文本生成
  - `generate_structured()`: 结构化 JSON 输出
  - `batch_generate()`: 批量生成

**环境变量:**
- `OPENROUTER_API_KEY`: 必需,OpenRouter API 密钥
- `DATABASE_URL`: SQLite 数据库路径
- `LITELLM_CONFIG_PATH`: 可选,默认 `./config/litellm_config.yaml`

### 4. 数据库设计 (schema.sql)

**关键表:**
1. `novels`: 小说元数据
2. `world_states`: 世界状态快照 (按 turn 版本化)
3. `chapters`: 章节内容
4. `event_nodes`: 事件节点 (包含评分指标)
5. `event_arcs`: 事件线
6. `clues`, `evidence`, `setup_debts`: 线索经济系统
7. `execution_logs`: 执行日志 (用于检测停滞)
8. `characters`: 角色持久化

**数据库工具:** `src/utils/database.py`
- `Database` 类提供完整 CRUD 操作
- 方法: `save_world_state()`, `save_chapter()`, `get_novel()`, etc.
- 默认schema路径: `database/schema/core.sql`

### 5. Web 服务架构

**后端 (FastAPI) - 分层架构:**
- 入口: `web/backend/main.py`
- 启动事件中初始化 LiteLLM 和 Database (使用绝对路径)
- 目录结构:
  - `api/`: API路由层 (chat_api, game_api, world_api, generation_api)
  - `services/`: 业务逻辑层 (world_generator, scene_refinement, agent_generation)
  - `game/`: 游戏引擎 (game_engine, game_tools, quests)
  - `models/`: 数据模型 (world_models)
  - `database/`: 数据库访问 (world_db)
  - `llm/`: LLM集成层
- REST API: `/api/novels`, `/api/game`, `/api/world`, `/api/chat`
- WebSocket: `/ws/generate/{novel_id}` 用于实时章节生成
- API 文档: http://localhost:8000/docs

**前端 (Next.js 14):**
- 框架: Next.js 14 App Router + TypeScript
- UI: shadcn/ui (基于 Radix UI)
- 样式: Tailwind CSS
- 页面结构:
  - `app/page.tsx`: 主页面
  - `app/chat/`: 聊天页面
  - `app/game/`: 游戏页面
  - `app/world/`: 世界管理页面
- 组件结构:
  - `components/chat/`: 聊天相关组件
  - `components/novel/`: 小说相关组件
  - `components/world/`: 世界管理组件
  - `components/ui/`: shadcn/ui 组件

## 开发注意事项

### 路径解析规则

**后端启动时必须使用绝对路径:**
```python
# web/backend/main.py 中的正确做法
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
config_path = project_root / "config" / "litellm_config.yaml"
db_path = project_root / "data" / "sqlite" / "novel.db"

llm_client = LiteLLMClient(config_path=str(config_path))
db = Database(db_path=str(db_path))
```

**原因:** FastAPI 的工作目录可能不是项目根目录,相对路径会失败。

### LiteLLM 配置

1. **环境变量替换:** 配置中的 `${OPENROUTER_API_KEY}` 会自动替换为 `.env` 中的值
2. **Router 参数:** 使用 `default_max_parallel_requests` 而非 `max_parallel_requests`
3. **Fallbacks:** 当前配置已简化,移除了复杂的 fallbacks 配置

### 前端依赖管理

**shadcn/ui 组件依赖:**
- 每个 shadcn/ui 组件可能需要对应的 `@radix-ui/*` 包
- 例如: `radio-group.tsx` 需要 `@radix-ui/react-radio-group`
- 添加新组件后,检查并安装缺失的依赖

**清理缓存:**
```bash
cd web/frontend
rm -rf .next
npm install
```

### Character 初始化

Character 对象需要 `description` 参数:
```python
protagonist = Character(
    id="PROTAGONIST",
    name="主角名",
    role="protagonist",
    description="角色描述",  # 必需!
    attributes={...},
    resources={...}
)
```

### 模型选择

当前配置下,所有章节生成都使用 DeepSeek V3:
```python
# interactive_generator.py 中
model = "deepseek"  # 所有章节都用 DeepSeek
```

这是有意的设计,因为:
- DeepSeek V3 性价比极高
- 中文生成质量优秀
- 适合大量章节生成

## 常见问题排查

### 后端启动失败: "配置文件不存在"
- 检查 `web/backend/main.py` 是否使用绝对路径
- 确认项目根目录下存在 `config/litellm_config.yaml`

### 前端编译失败: "Module not found"
- 检查 `package.json` 是否包含所需的 `@radix-ui/*` 依赖
- 运行 `npm install`
- 清理 `.next` 缓存后重试

### LiteLLM Router 初始化错误
- 检查 `router_settings` 中的参数名称
- 确认 `.env` 中的 `OPENROUTER_API_KEY` 已设置
- 验证模型名称格式: `openrouter/provider/model-name`

### Character 初始化错误
- 确保传入 `description` 参数
- 可以从 setting JSON 的 `职业` 字段获取默认值

### 数据库连接失败
- 确认 `data/sqlite/` 目录存在
- 运行 `python scripts/init_db.py` 初始化数据库
- 检查文件权限

## 项目状态

**已实现功能:**
- ✅ LiteLLM 多模型路由 (OpenRouter)
- ✅ SQLite 数据库 Schema 和 CRUD
- ✅ 基础数据模型 (WorldState, Character, EventNode, etc.)
- ✅ CLI 交互式生成器
- ✅ FastAPI Web 后端
- ✅ Next.js + shadcn/ui 前端
- ✅ WebSocket 实时生成 (基础版本)
- ✅ 聊天界面流式输出 (LiteLLM + DeepSeek V3)
- ✅ 小说设定自动加载 (避免重复输入)
- ✅ 快捷生成按钮 (下一章/对话/场景/伏笔)

**部分实现:**
- ⚠️ Global Director (结构已定义,评分系统未完全实现)
- ⚠️ 一致性审计系统 (框架存在,逻辑待完善)
- ⚠️ 线索经济管理 (数据模型就绪,业务逻辑待开发)

**未实现:**
- ❌ MCP Server 集成
- ❌ Claude Agent SDK 集成
- ❌ 向量数据库 (ChromaDB/FAISS)
- ❌ 完整的事件线生成与调度
- ❌ 伏笔债务 SLA 检查

## 目录结构

项目采用清晰的分层目录结构:

```
mn_xiao_shuo/
├── database/schema/          # 数据库schema文件
├── docs/                     # 文档（分类管理）
│   ├── features/            # 功能文档
│   ├── setup/               # 设置指南
│   ├── implementation/      # 实现细节
│   ├── operations/          # 运维文档
│   ├── troubleshooting/     # 故障排除
│   └── reference/           # 参考文档
├── scripts/                  # 脚本工具
│   ├── start/               # 启动脚本
│   ├── dev/                 # 开发工具
│   └── test/                # 测试脚本
├── tests/                    # 测试代码
│   ├── integration/         # 集成测试
│   └── e2e/                 # 端到端测试
└── web/backend/              # 后端服务
    ├── api/                 # API路由层
    ├── services/            # 业务逻辑层
    ├── game/                # 游戏引擎
    ├── models/              # 数据模型
    └── database/            # 数据库访问
```

详细说明: `docs/DIRECTORY_STRUCTURE.md`

## 相关文档

**快速开始:**
- `README.md`: 项目概览和快速开始
- `docs/guides/QUICK_START.md`: 快速启动指南
- `docs/guides/START_HERE.md`: 新手入门

**架构设计:**
- `docs/architecture/ARCHITECTURE.md`: 详细架构设计文档
- `docs/architecture/PROJECT_SUMMARY.md`: 项目总结
- `docs/architecture/IMPROVEMENTS_SUMMARY.md`: 改进总结

**功能文档:**
- `docs/features/WORLD_SCAFFOLD_GUIDE.md`: 世界脚手架指南
- `docs/features/QUEST_SYSTEM.md`: 任务系统
- `docs/features/GAME_FEATURES.md`: 游戏功能

**设置指南:**
- `docs/setup/SETUP_COMPLETE.md`: 完整设置指南
- `docs/guides/OPENROUTER_SETUP.md`: OpenRouter 配置
- `docs/setup/LITELLM_PROXY_SETUP.md`: LiteLLM Proxy 设置

**运维文档:**
- `docs/operations/START_ALL_WITH_AGENT_GUIDE.md`: 启动脚本指南
- `docs/operations/DEMO_EXPERIENCE_GUIDE.md`: 演示体验指南

**故障排除:**
- `docs/troubleshooting/TROUBLESHOOTING.md`: 故障排除指南
- `docs/troubleshooting/BUG_FIXES.md`: Bug修复日志

**参考:**
- `docs/reference/QUICK_REFERENCE.md`: 快速参考
- `docs/INDEX.md`: 完整文档索引
- `docs/DIRECTORY_STRUCTURE.md`: 目录结构说明
- `docs/MIGRATION_COMPLETE.md`: 目录重组报告
