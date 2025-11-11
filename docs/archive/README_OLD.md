# 已归档：早期小说生成器文档
<!-- moved to docs/archive on 2025-11-11 -->

此文档描述的是早期“长篇小说生成器（CLI/交互式）”版本，当前项目已聚焦于“AI 世界生成 + 跑团游戏（Web）”。

请参考以下最新文档：
- `README.md`（项目总览与快速开始）
- `docs/PROJECT_OVERVIEW.md`（完整概览与架构）
- `docs/WORLDPACK_QUICKSTART.md`（WorldPack 快速上手）

如需保留历史参考，可在版本控制中查看本文件的历史版本。

## 核心特性（历史版本，仅供参考）

- **全局导演系统**: 智能调度事件线，平衡可玩性与叙事完整性
- **一致性审计**: 自动检查硬规则、因果链、资源守恒
- **线索经济**: 管理伏笔、线索与证据的生命周期
- **多模型支持**: 通过 OpenRouter 支持 DeepSeek/Claude/GPT-4/Qwen
- **LangChain Agent**: 15个游戏工具，流式生成，工具调用
- **世界管理**: 世界脚手架系统，场景细化流水线

## 技术栈（历史版本，仅供参考）

- **Python 3.11+** + **uv** (包管理器)
- **LangChain 1.0**: Agent 框架
- **OpenRouter**: 多模型 API 网关
- **FastAPI**: 后端 Web 框架
- **Next.js 14**: 前端框架 + shadcn/ui
- **PostgreSQL + ChromaDB**: 状态存储与向量检索

## 快速开始

### 🚀 一键启动（推荐）

```bash
# 启动完整系统（Backend + Frontend）
./scripts/start/start_all_with_agent.sh

# 访问服务：
# - 前端界面: http://localhost:3000
# - API 文档: http://localhost:8000/docs
```

这会自动启动：
- **FastAPI Backend** (端口 8000) - LangChain Agent + 游戏工具
- **Next.js Frontend** (端口 3000) - Web 界面

详见 [docs/implementation/LANGCHAIN_MIGRATION_PLAN.md](docs/implementation/LANGCHAIN_MIGRATION_PLAN.md)

### 检查服务状态

```bash
# 查看所有服务状态
./check_services.sh

# 查看日志
tail -f logs/*.log
```

### 停止服务

```bash
# 停止所有服务
./stop_all.sh

# 或按 Ctrl+C
```

### CLI 交互模式

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行交互式生成器
python interactive_generator.py
```

### 开发环境设置

```bash
# 1. 安装依赖 (使用 uv)
uv pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 OPENROUTER_API_KEY

# 3. 初始化数据库
python scripts/init_db.py

# 4. 测试配置
python tests/integration/test_setup.py
```

## 项目结构

```
mn_xiao_shuo/
├── README.md                    # 本文件
├── CLAUDE.md                    # Claude Code 开发指南
├── schema.sql                   # 数据库 Schema
├── interactive_generator.py     # CLI 交互式生成器
│
├── docs/                        # 📚 文档
│   ├── INDEX.md                 # 文档索引
│   ├── architecture/            # 架构设计
│   │   ├── ARCHITECTURE.md
│   │   └── PROJECT_SUMMARY.md
│   └── guides/                  # 开发指南
│       ├── QUICK_START.md
│       ├── OPENROUTER_SETUP.md
│       └── ...
│
├── web/                         # 🌐 Web 服务
│   ├── QUICKSTART.md           # Web 快速启动
│   ├── backend/                # FastAPI 后端
│   │   └── main.py
│   └── frontend/               # Next.js 前端
│       ├── app/
│       └── components/
│
├── src/                        # 💻 源代码
│   ├── models/                 # 数据模型
│   │   ├── world_state.py
│   │   ├── event_node.py
│   │   ├── action_queue.py
│   │   └── clue.py
│   ├── llm/                    # LLM 集成
│   │   └── litellm_client.py
│   ├── utils/                  # 工具函数
│   │   └── database.py
│   ├── director/               # 全局导演 (待实现)
│   └── mcp_server/             # MCP 服务器 (待实现)
│
├── config/                     # ⚙️ 配置
│   └── litellm_config.yaml
│
├── scripts/                    # 🔧 脚本
│   └── init_db.py
│
├── tests/                      # 🧪 测试
│   └── integration/
│       ├── test_database.py
│       ├── test_openrouter.py
│       └── test_setup.py
│
├── examples/                   # 📝 示例
│   ├── scifi_setting.json
│   └── xianxia_setting.json
│
├── outputs/                    # 📖 生成的小说
│   └── output_novel_*.md
│
├── data/                       # 💾 数据
│   └── sqlite/
│       └── novel.db
│
└── logs/                       # 📋 日志
```

查看完整文档索引: [docs/INDEX.md](docs/INDEX.md)

## 使用示例

### 创建科幻小说

```python
from src.director.gd import GlobalDirector, NovelType, Preference

# 加载设定
with open("examples/scifi_setting.json") as f:
    setting = json.load(f)

# 创建导演
director = GlobalDirector(
    setting=setting,
    novel_type=NovelType.SCIFI,
    preference=Preference.HYBRID
)

# 生成章节
async for scene in director.run_scene_loop():
    print(scene["content"])
```

### 自定义设定

```json
{
  "setting_text": "2157年，地球联邦发现可控核聚变技术突破...",
  "experience_goal": "揭露能源垄断 + 科技谍战 + 政治博弈",
  "preference": "hybrid",
  "constraints": {
    "hard_rules": ["能量守恒", "光速限制", "因果律"],
    "content_guard": ["无现实危险技术细节"]
  },
  "hint_policy": {
    "hint_latency": 2,
    "explicit_ratio": 0.3,
    "red_herring_cap": 1
  }
}
```

## 配置说明

### LiteLLM 模型配置

编辑 `config/litellm_config.yaml`:

```yaml
model_list:
  - model_name: claude-sonnet
    litellm_params:
      model: anthropic/claude-sonnet-4-5-20250929
      api_key: ${ANTHROPIC_API_KEY}

router_settings:
  routing_strategy: least-busy
  fallbacks: ["claude-sonnet", "gpt-4"]
```

### 小说类型参数

编辑 `config/novel_types.yaml` 调整不同类型的评分权重和节奏参数。

## 开发路线图

- [x] 架构设计
- [x] MVP 核心功能
  - [x] LiteLLM 集成 (OpenRouter)
  - [x] SQLite 状态存储
  - [x] CLI 交互界面
  - [x] Web 服务 (FastAPI + Next.js)
  - [ ] Global Director 完整实现
- [ ] 增强功能
  - [ ] MCP Server
  - [ ] Claude Agent SDK
  - [ ] 向量数据库 (ChromaDB)
  - [ ] 一致性审计系统
  - [ ] 线索经济完整实现
- [ ] 产品化
  - [x] Web API 基础版本
  - [ ] 用户认证
  - [ ] 导出功能 (EPUB)
  - [ ] 部署脚本

详见 [docs/guides/NEXT_STEPS.md](docs/guides/NEXT_STEPS.md)

## 贡献

欢迎提交 Issue 和 Pull Request!

## 许可证

MIT License
