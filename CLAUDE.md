# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于 AI 驱动的长篇小说生成系统,支持科幻和玄幻/仙侠两大类型。系统采用"全局导演"(Global Director)架构,通过事件线评分、一致性审计和线索经济管理来生成连贯的长篇小说。

**最新更新(2025-01-31)**: 实现了完整的全局导演架构,包括:
- ✅ 可编辑设定系统(支持动态修改世界观、主角、路线)
- ✅ NPC按需生成机制(seed→instantiate→engage→adapt→retire)
- ✅ 事件线评分系统(可玩性/叙事/混合三种模式)
- ✅ 线索经济管理(伏笔SLA、证据链验证、健康度监控)
- ✅ 一致性审计系统(硬规则/因果/资源/角色/时间线检查)
- ✅ 会话历史管理(完整记录、支持分支、智能上下文)

详见: `docs/architecture/IMPROVEMENTS_SUMMARY.md` 和 `docs/QUICK_REFERENCE.md`

## 关键命令

### 开发环境设置

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖 (首次运行)
cd web/frontend && npm install && cd ../..

# 初始化数据库
python scripts/init_db.py
```

### 运行服务

```bash
# 一键启动 Web 服务 (后端 + 前端)
./web/start-web.sh

# 或手动启动后端 (端口 8000)
source .venv/bin/activate
cd web/backend
uvicorn main:app --reload --port 8000

# 或手动启动前端 (端口 3000)
cd web/frontend
npm run dev

# CLI 交互式生成
python interactive_generator.py
```

### 测试

```bash
# 测试数据库连接
python test_database.py

# 测试 OpenRouter API
python test_openrouter.py

# 测试完整设置
python test_setup.py
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

### 5. Web 服务架构

**后端 (FastAPI):**
- 入口: `web/backend/main.py`
- 启动事件中初始化 LiteLLM 和 Database (使用绝对路径)
- REST API: `/api/novels`, `/api/novels/{id}`, `/api/novels/{id}/chapters/{num}`
- WebSocket: `/ws/generate/{novel_id}` 用于实时章节生成
- API 文档: http://localhost:8000/docs

**前端 (Next.js 14):**
- 框架: Next.js 14 App Router + TypeScript
- UI: shadcn/ui (基于 Radix UI)
- 样式: Tailwind CSS
- 组件结构:
  - `app/page.tsx`: 主页面,包含 Tabs
  - `components/novel/novel-generator.tsx`: 小说生成界面
  - `components/novel/novel-list.tsx`: 小说列表
  - `components/ui/*`: shadcn/ui 组件

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

## 相关文档

- `README.md`: 项目概览和快速开始
- `docs/architecture/ARCHITECTURE.md`: 详细架构设计文档
- `docs/architecture/PROJECT_SUMMARY.md`: 项目总结
- `docs/guides/QUICK_START.md`: 快速启动指南
- `docs/guides/OPENROUTER_SETUP.md`: OpenRouter 配置指南
- `docs/guides/IMPLEMENTATION_GUIDE.md`: 实现指南
- `web/QUICKSTART.md`: Web 服务快速启动指南
- `web/STREAMING_IMPLEMENTATION.md`: 流式输出实现说明
- `schema.sql`: 完整数据库 Schema
- `docs/INDEX.md`: 完整文档索引
