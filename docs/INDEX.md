# 项目文档索引

## 📚 快速导航

### 新手入门
1. **[README.md](../README.md)** - 项目概览、快速开始、技术栈
2. **[CLAUDE.md](../CLAUDE.md)** - Claude Code 开发指南 (必读)
3. **[guides/QUICK_START.md](guides/QUICK_START.md)** - 快速启动指南
4. **[guides/START_HERE.md](guides/START_HERE.md)** - 从这里开始

### Web 服务
- **[../web/QUICKSTART.md](../web/QUICKSTART.md)** - Web 服务一键启动指南
- **[../web/README.md](../web/README.md)** - Web 服务详细说明

### 架构与设计
- **[architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)** - 完整系统架构设计
- **[architecture/PROJECT_SUMMARY.md](architecture/PROJECT_SUMMARY.md)** - 项目总结与进展

### 开发指南
- **[guides/IMPLEMENTATION_GUIDE.md](guides/IMPLEMENTATION_GUIDE.md)** - 实现指南
- **[guides/OPENROUTER_SETUP.md](guides/OPENROUTER_SETUP.md)** - OpenRouter API 配置
- **[guides/CHECKLIST.md](guides/CHECKLIST.md)** - 开发检查清单
- **[guides/NEXT_STEPS.md](guides/NEXT_STEPS.md)** - 下一步计划

### 技术参考
- **[../schema.sql](../schema.sql)** - 完整数据库 Schema
- **[../config/litellm_config.yaml](../config/litellm_config.yaml)** - LiteLLM 模型配置

### 示例与输出
- **[../examples/](../examples/)** - 小说设定示例
- **[../outputs/](../outputs/)** - 生成的小说输出

### 测试
- **[../tests/integration/](../tests/integration/)** - 集成测试脚本
  - `test_database.py` - 数据库测试
  - `test_openrouter.py` - OpenRouter API 测试
  - `test_setup.py` - 完整设置测试

## 📂 目录结构

```
mn_xiao_shuo/
├── README.md                    # 项目主文档
├── CLAUDE.md                    # Claude Code 开发指南
├── schema.sql                   # 数据库 Schema
│
├── docs/                        # 文档目录
│   ├── INDEX.md                 # 本索引文件
│   ├── architecture/            # 架构设计文档
│   │   ├── ARCHITECTURE.md
│   │   └── PROJECT_SUMMARY.md
│   └── guides/                  # 开发指南
│       ├── QUICK_START.md
│       ├── START_HERE.md
│       ├── IMPLEMENTATION_GUIDE.md
│       ├── OPENROUTER_SETUP.md
│       ├── CHECKLIST.md
│       └── NEXT_STEPS.md
│
├── src/                         # 源代码
│   ├── models/                  # 数据模型
│   ├── llm/                     # LLM 集成
│   ├── utils/                   # 工具函数
│   ├── director/                # 全局导演 (待实现)
│   └── mcp_server/              # MCP 服务器 (待实现)
│
├── web/                         # Web 服务
│   ├── QUICKSTART.md
│   ├── README.md
│   ├── backend/                 # FastAPI 后端
│   │   └── main.py
│   └── frontend/                # Next.js 前端
│       ├── app/
│       └── components/
│
├── config/                      # 配置文件
│   └── litellm_config.yaml
│
├── scripts/                     # 脚本工具
│   └── init_db.py
│
├── tests/                       # 测试
│   └── integration/             # 集成测试
│       ├── test_database.py
│       ├── test_openrouter.py
│       └── test_setup.py
│
├── examples/                    # 示例设定
│   ├── scifi_setting.json
│   └── xianxia_setting.json
│
├── outputs/                     # 生成的小说
│   └── output_novel_*.md
│
├── data/                        # 数据存储
│   └── sqlite/
│       └── novel.db
│
└── logs/                        # 日志文件
```

## 🎯 按任务查找文档

### 我想启动服务
→ [web/QUICKSTART.md](../web/QUICKSTART.md) 或 [guides/QUICK_START.md](guides/QUICK_START.md)

### 我想了解系统架构
→ [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)

### 我想配置 AI 模型
→ [guides/OPENROUTER_SETUP.md](guides/OPENROUTER_SETUP.md)

### 我想理解代码结构
→ [CLAUDE.md](../CLAUDE.md) 的"核心架构"部分

### 我想添加新功能
→ [guides/IMPLEMENTATION_GUIDE.md](guides/IMPLEMENTATION_GUIDE.md)

### 我想测试系统
→ [../tests/integration/](../tests/integration/) 目录

### 我想查看生成的小说
→ [../outputs/](../outputs/) 目录

## 📝 文档维护

- 所有架构相关文档放在 `docs/architecture/`
- 所有操作指南放在 `docs/guides/`
- Web 服务文档保留在 `web/` 目录下
- 生成的输出放在 `outputs/` 目录
- 测试脚本放在 `tests/integration/` 目录
