# 项目文档索引

## 📚 快速导航

### 新手入门
1. `../README.md` - 项目概览、快速开始、技术栈
2. `docs/PROJECT_OVERVIEW.md` - 完整项目概览与路线图
3. `docs/WORLDPACK_QUICKSTART.md` - WorldPack 世界生成快速上手
4. `docs/guides/OPENROUTER_SETUP.md` - OpenRouter 配置

### 架构与设计
- `docs/architecture/ARCHITECTURE.md` - 系统架构设计
- `docs/TECHNICAL_ARCHITECTURE.md` - 技术架构详解

### 功能与实现
- `docs/features/GAME_UI_GUIDE.md` - 游戏UI指南
- `docs/implementation/PHASE2_API_ENDPOINTS.md` - API端点文档
- `docs/implementation/GLOBAL_DIRECTOR_IMPLEMENTATION.md` - 全局导演实现

### 运维与排障
- `docs/operations/` - 优化阶段与运维记录
- `docs/troubleshooting/TROUBLESHOOTING.md` - 常见问题

## 📂 目录结构（简版）

```
mn_xiao_shuo/
├── README.md                 # 主文档（推荐从这里开始）
├── docs/                     # 文档（本目录）
│   ├── PROJECT_OVERVIEW.md
│   ├── WORLDPACK_QUICKSTART.md
│   ├── architecture/
│   ├── features/
│   ├── implementation/
│   ├── operations/
│   └── troubleshooting/
├── web/                      # Web 应用（Next.js + FastAPI）
│   ├── backend/
│   └── frontend/
├── scripts/
└── tests/
```

## 🎯 按任务查找

- 启动项目 → `../README.md` 的“快速开始”
- 生成世界 → `docs/WORLDPACK_QUICKSTART.md`
- 查看架构 → `docs/architecture/ARCHITECTURE.md`
- API参考 → `docs/implementation/PHASE2_API_ENDPOINTS.md`
- 常见问题 → `docs/troubleshooting/TROUBLESHOOTING.md`

## 📝 维护约定

- 新功能文档优先放入 `docs/features/` 或 `docs/implementation/`
- 运维日志、阶段总结放入 `docs/operations/`
- 历史或已淘汰文档移入 `docs/archive/`
