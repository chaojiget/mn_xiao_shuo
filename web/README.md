# Web 应用概览（Next.js + FastAPI）

> 当前应用聚焦于 AI 世界生成与单人跑团游戏：支持 WorldPack 世界预生成、AI DM 实时叙事、任务/NPC/存档系统等。

## 技术栈

### 前端
- Next.js 14（App Router）
- TypeScript + Tailwind CSS + shadcn/ui
- Zustand 状态管理
- WebSocket 流式交互

### 后端
- FastAPI + Uvicorn
- LangChain 1.0（Agent + 工具）
- OpenRouter（DeepSeek/Claude/GPT/Qwen）
- SQLite（存档/世界数据/索引）

## 目录结构

```
web/
├── backend/               # FastAPI 后端
│   ├── api/              # API 路由（game_api.py / dm_api.py / worlds_api.py）
│   ├── agents/           # DM Agent 与工具
│   ├── services/         # 世界生成/索引/存档等服务
│   └── models/           # Pydantic 数据模型
└── frontend/              # Next.js 前端
    ├── app/              # 页面（/game, /worlds 等）
    └── components/game/  # 游戏组件（DmInterface/QuestTracker等）
```

## 快速开始

### 推荐：一键启动
```bash
./scripts/start/start_all_with_agent.sh
```

这会启动：
- 后端 API: http://localhost:8000
- 前端 UI: http://localhost:3000
- API 文档: http://localhost:8000/docs

### 手动启动
```bash
# 后端
cd web/backend
uv run uvicorn main:app --reload --port 8000

# 前端
cd web/frontend
npm install
npm run dev
```

## 关键页面与端点

- 世界管理（WorldPack）: http://localhost:3000/worlds
- 跑团游戏页面: http://localhost:3000/game/play
- DM WebSocket 路由: [backend/api/dm_api.py](backend/api/dm_api.py)
- API 端点文档: [docs/implementation/PHASE2_API_ENDPOINTS.md](../docs/implementation/PHASE2_API_ENDPOINTS.md)

## 功能特性

- ✅ WorldPack 世界预生成（地点/NPC/任务/掉落/遭遇）
- ✅ AI DM 实时叙事（WebSocket 流式）
- ✅ 任务与NPC系统
- ✅ 自动保存 + 多槽位存档
- ✅ 世界语义索引与检索（可回退哈希向量）

更多细节见 [docs/PROJECT_OVERVIEW.md](../docs/PROJECT_OVERVIEW.md) 与 [docs/WORLDPACK_QUICKSTART.md](../docs/WORLDPACK_QUICKSTART.md)。
