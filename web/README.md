# 长篇小说生成系统 - Web 服务

基于 **shadcn/ui** 的现代化 Web 界面，支持实时小说生成和交互。

## 技术栈

### 前端
- **Next.js 14** - React 框架
- **shadcn/ui** - 组件库
- **Tailwind CSS** - 样式
- **TypeScript** - 类型安全
- **WebSocket** - 实时通信

### 后端
- **FastAPI** - Python Web 框架
- **WebSocket** - 实时推送
- **SQLite** - 数据存储
- **LiteLLM** - LLM 集成

## 项目结构

```
web/
├── frontend/              # Next.js 前端
│   ├── app/              # App Router
│   ├── components/       # React 组件
│   │   ├── ui/          # shadcn/ui 组件
│   │   └── novel/       # 业务组件
│   ├── lib/             # 工具函数
│   └── public/          # 静态资源
│
└── backend/              # FastAPI 后端
    ├── api/             # API 路由
    ├── services/        # 业务逻辑
    └── models/          # 数据模型
```

## 快速开始

### 1. 安装前端依赖

```bash
cd web/frontend
npm install
```

### 2. 启动后端

```bash
cd web/backend
source ../../.venv/bin/activate
uvicorn main:app --reload
```

### 3. 启动前端

```bash
cd web/frontend
npm run dev
```

访问 http://localhost:3000

## 功能特性

- ✅ 实时小说生成
- ✅ 交互式选择
- ✅ 章节管理
- ✅ 导出功能
- ✅ 暗黑模式
- ✅ 响应式设计
