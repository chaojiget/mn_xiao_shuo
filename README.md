# AI 世界生成器

> 基于 AI 的完整世界生成系统，支持预构建世界和动态游戏体验

## 🎯 核心功能

### 1. WorldPack 世界生成系统
- **自动生成完整世界**: 地点、NPC、任务、战利品表、遭遇表
- **8阶段生成流水线**: OUTLINE → LOCATIONS → NPCS → QUESTS → LOOT_TABLES → ENCOUNTER_TABLES → INDEXING → READY
- **可定制参数**: 基调(epic/dark/cozy/mystery/whimsical)、难度(story/normal/hard)、规模
- **世界管理**: 校验、快照、发布功能

### 2. AI 地下城主系统
- **智能DM**: 基于 LangChain 1.0 的 AI 地下城主
- **15个游戏工具**: 状态管理、检定、任务、NPC等
- **流式响应**: WebSocket 实时对话
- **动态叙事**: 根据玩家行动生成独特故事

### 3. 进度管理系统
- **自动保存**: 每回合自动保存到槽位0
- **多槽位存档**: 支持10个手动存档槽位
- **智能恢复**: 自动检测worldId，恢复正确进度

## 🚀 快速开始

### 前置要求
- Node.js 18+
- Python 3.10+
- uv (Python包管理器)
- OpenRouter API Key

### 安装依赖

```bash
# 后端依赖
uv pip install -r requirements.txt

# 前端依赖
cd web/frontend
npm install
```

### 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，填入你的 API Key
OPENROUTER_API_KEY=your_key_here
```

### 启动服务

```bash
# 方式1: 使用启动脚本（推荐）
./scripts/start/start_all_with_agent.sh

# 方式2: 手动启动后端
cd web/backend
uv run uvicorn main:app --reload --port 8000

# 方式2: 手动启动前端
cd web/frontend
npm run dev
```

### 访问应用

- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 📖 使用指南

### 1. 生成世界

1. 访问 http://localhost:3000/worlds
2. 点击"生成新世界"
3. 填写参数:
   - 标题: 你的世界名称
   - 基调: epic/dark/cozy/mystery/whimsical
   - 难度: story/normal/hard
   - 地点数: 5-15
   - NPC数: 8-20
   - 任务数: 3-10
4. 点击"开始生成"，等待约60秒
5. 自动跳转到世界详情页

### 2. 开始冒险

1. 在世界详情页点击"开始冒险"
2. 如有进度，选择"继续"或"重新开始"
3. 进入游戏界面
4. 在输入框中输入你的行动
5. AI DM会响应并推进故事

### 3. 管理进度

- **自动保存**: 每回合自动保存
- **手动保存**: 点击"保存到槽位"，选择槽位1-10
- **读取存档**: 点击"读取槽位"，选择要恢复的槽位
- **重新开始**: 点击"重新开始"按钮

## 🏗️ 项目结构

```
mn_xiao_shuo/
├── web/
│   ├── backend/               # FastAPI 后端
│   │   ├── api/              # API路由层
│   │   ├── services/         # 业务逻辑层
│   │   ├── agents/           # LangChain Agent
│   │   ├── game/             # 游戏引擎
│   │   ├── models/           # 数据模型
│   │   └── llm/              # LLM集成
│   └── frontend/             # Next.js 前端
│       ├── app/              # 页面路由
│       │   ├── page.tsx      # 首页
│       │   ├── worlds/       # 世界管理
│       │   └── game/         # 游戏页面
│       └── components/       # UI组件
├── database/schema/          # 数据库schema
├── docs/                     # 文档
├── scripts/                  # 工具脚本
└── tests/                    # 测试代码
```

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI
- **AI**: LangChain 1.0 + OpenRouter
- **模型**: DeepSeek V3, Claude 3.5 Sonnet, GPT-4, Qwen 2.5
- **数据库**: SQLite
- **包管理**: uv

### 前端
- **框架**: Next.js 14 (App Router)
- **UI**: shadcn/ui (Radix UI + Tailwind CSS)
- **类型**: TypeScript
- **状态管理**: Zustand

## 📚 文档

- [WorldPack到冒险指南](docs/WORLDPACK_TO_ADVENTURE.md) - 完整使用流程
- [快速开始](docs/WORLDPACK_QUICKSTART.md) - 5分钟快速体验
- [端到端测试](tests/e2e/test_world_to_game_ui.md) - UI测试指南

## 🐛 故障排除

### 后端启动失败
```bash
# 检查数据库
python scripts/init_db.py

# 检查依赖
uv pip install -r requirements.txt
```

### 前端构建失败
```bash
cd web/frontend
rm -rf .next node_modules
npm install
npm run build
```

### WebSocket连接失败
- 确认后端已启动在8000端口
- 检查CORS配置
- 查看浏览器控制台错误

## 🎮 游戏特性

- ✅ 预生成完整世界（地点、NPC、任务）
- ✅ AI驱动的地下城主
- ✅ 动态对话系统
- ✅ 自动保存与多槽位存档
- ✅ 智能进度恢复
- ✅ 基于坐标的地图系统
- ✅ 任务追踪与目标管理
- ✅ 难度自适应（HP、金币等）
- ✅ 定制化开场白（根据世界基调）

## 📊 版本信息

- **当前版本**: v1.2
- **WorldPack**: 完整功能
- **进度管理**: 智能恢复
- **最后更新**: 2025-11-11

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**快速开始**: 访问 http://localhost:3000 开始你的冒险！🎮
