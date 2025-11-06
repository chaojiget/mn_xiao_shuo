# start_all_with_agent.sh 完整启动指南

## 概述

`start_all_with_agent.sh` 是一键启动脚本，会同时启动：
1. **LiteLLM Proxy** (端口 4000) - LLM 路由服务
2. **FastAPI Backend** (端口 8000) - 后端 API 服务
3. **Next.js Frontend** (端口 3000) - 前端界面

所有服务都会自动配置为使用 LiteLLM Proxy 和 DeepSeek 模型。

## 快速开始

```bash
# 一键启动所有服务
./start_all_with_agent.sh

# 停止所有服务
./stop_all.sh

# 或按 Ctrl+C 停止
```

## 服务架构

```
┌─────────────────┐
│  用户浏览器      │
│  localhost:3000 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Next.js        │
│  Frontend       │
│  Port 3000      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI        │
│  Backend        │
│  Port 8000      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LiteLLM Proxy  │
│  Port 4000      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  OpenRouter     │
│  DeepSeek V3    │
└─────────────────┘
```

## 环境变量配置

### 自动配置

脚本会自动设置以下环境变量：

```bash
# LiteLLM Proxy 认证
LITELLM_MASTER_KEY=sk-litellm-xxxxxxxxxxxxxxxx  # 自动生成

# Claude Agent SDK 配置（指向 LiteLLM Proxy）
ANTHROPIC_BASE_URL=http://0.0.0.0:4000
ANTHROPIC_AUTH_TOKEN=$LITELLM_MASTER_KEY
ANTHROPIC_MODEL=openrouter/deepseek/deepseek-v3.1-terminus-v3-0324
```

### 必需的环境变量（.env 文件）

启动前确保 `.env` 文件包含：

```bash
# OpenRouter API Key（必需）
OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

## 启动流程详解

### 1. 初始化阶段

```bash
🚀 启动 AI 跑团小说系统（完整版）
==============================================
📝 加载环境变量...
```

- 激活虚拟环境 `.venv`
- 加载 `.env` 文件
- 检查 `OPENROUTER_API_KEY` 是否设置

### 2. 生成认证密钥

```bash
🔑 生成 LITELLM_MASTER_KEY...
✅ 已保存 LITELLM_MASTER_KEY 到 .env
```

- 如果 `LITELLM_MASTER_KEY` 不存在，自动生成
- 保存到 `.env` 文件
- 同时保存 Claude Agent SDK 的配置

### 3. 启动 LiteLLM Proxy

```bash
📦 检查 LiteLLM Proxy 安装...
🤖 启动 LiteLLM Proxy (端口 4000)...
   PID: 12345
⏳ 等待 LiteLLM Proxy 启动...
✅ LiteLLM Proxy 启动成功
```

- 检查并安装 `litellm[proxy]`
- 启动 LiteLLM Proxy (使用 `config/litellm_config.yaml`)
- 等待 5 秒确保服务启动
- 健康检查 `http://localhost:4000/health`

### 4. 启动 FastAPI Backend

```bash
🔧 启动 FastAPI 后端 (端口 8000)...
   PID: 12346
⏳ 等待后端启动...
✅ 后端启动成功
```

- 使用 `uv run uvicorn` 启动
- 启用热重载 `--reload`
- 日志输出到 `logs/backend.log`

### 5. 启动 Next.js Frontend

```bash
🎨 启动 Next.js 前端 (端口 3000)...
   PID: 12347
```

- 使用 `npm run dev` 启动开发服务器
- 日志输出到 `logs/frontend.log`

### 6. 启动完成

```bash
==============================================
✅ 所有服务已启动！

📍 LiteLLM Proxy:  http://localhost:4000
📍 后端 API:       http://localhost:8000
📍 API 文档:       http://localhost:8000/docs
📍 前端界面:       http://localhost:3000

🤖 Claude Agent SDK 配置:
   ANTHROPIC_BASE_URL=http://0.0.0.0:4000
   ANTHROPIC_MODEL=openrouter/deepseek/deepseek-v3.1-terminus-v3-0324

📊 进程 ID:
   LiteLLM Proxy: 12345
   Backend:       12346
   Frontend:      12347

📝 日志文件:
   logs/litellm.log
   logs/backend.log
   logs/frontend.log

🛑 停止所有服务:
   kill 12345 12346 12347
   或运行: ./stop_all.sh
==============================================

按 Ctrl+C 停止所有服务...
```

## 访问服务

### 前端界面
打开浏览器访问: http://localhost:3000

### API 文档
查看 FastAPI 自动生成的文档: http://localhost:8000/docs

### LiteLLM Proxy 测试

```bash
# 获取可用模型列表
curl http://localhost:4000/v1/models

# 测试 DeepSeek 模型
curl -X POST http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -d '{
    "model": "deepseek",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

## 停止服务

### 方式1: 使用 stop_all.sh

```bash
./stop_all.sh
```

输出：
```
🛑 停止 AI 跑团小说系统...
================================
停止 LiteLLM Proxy (PID: 12345)...
  ✅ 已停止
停止 Backend (PID: 12346)...
  ✅ 已停止
停止 Frontend (PID: 12347)...
  ✅ 已停止

检查端口占用...
  端口 4000 (LiteLLM) 已清理
  端口 8000 (Backend) 已清理
  端口 3000 (Frontend) 已清理
  已清理所有 litellm 进程

✅ 所有服务已停止
================================
```

### 方式2: Ctrl+C

在运行 `start_all_with_agent.sh` 的终端按 `Ctrl+C`：

```bash
^C
✅ 所有服务已停止
```

### 方式3: 手动停止

```bash
# 使用保存的 PID
kill $(cat .pids/litellm.pid)
kill $(cat .pids/backend.pid)
kill $(cat .pids/frontend.pid)

# 或强制清理端口
lsof -ti:4000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

## 日志查看

### 实时查看所有日志

```bash
# LiteLLM Proxy
tail -f logs/litellm.log

# Backend
tail -f logs/backend.log

# Frontend
tail -f logs/frontend.log

# 同时查看所有
tail -f logs/*.log
```

### 检查错误

```bash
# 查找错误信息
grep -i error logs/*.log

# 查找警告
grep -i warning logs/*.log
```

## 常见问题

### Q1: 启动失败 - "OPENROUTER_API_KEY 未设置"

**解决方案**:
```bash
echo "OPENROUTER_API_KEY=sk-or-v1-xxxxx" >> .env
```

### Q2: LiteLLM Proxy 启动失败

**检查日志**:
```bash
cat logs/litellm.log
```

**常见原因**:
- 端口 4000 被占用：`lsof -ti:4000 | xargs kill -9`
- 配置文件错误：检查 `config/litellm_config.yaml`
- litellm 未安装：`uv pip install 'litellm[proxy]'`

### Q3: Backend 启动失败

**检查日志**:
```bash
cat logs/backend.log
```

**常见原因**:
- 端口 8000 被占用
- 数据库未初始化：`python scripts/init_db.py`
- 依赖未安装：`uv pip install -r requirements.txt`

### Q4: Frontend 启动失败

**检查日志**:
```bash
cat logs/frontend.log
```

**常见原因**:
- Node 模块未安装：`cd web/frontend && npm install`
- 端口 3000 被占用

### Q5: Claude Agent SDK 无法连接到 LiteLLM

**检查环境变量**:
```bash
echo $ANTHROPIC_BASE_URL
echo $ANTHROPIC_AUTH_TOKEN
echo $ANTHROPIC_MODEL
```

**确保设置正确**:
```bash
export ANTHROPIC_BASE_URL=http://0.0.0.0:4000
export ANTHROPIC_AUTH_TOKEN=$(grep LITELLM_MASTER_KEY .env | cut -d '=' -f2-)
export ANTHROPIC_MODEL=openrouter/deepseek/deepseek-v3.1-terminus-v3-0324
```

## 修改的文件列表

本次更新修改了以下文件：

### 启动脚本
- ✅ `start_all_with_agent.sh` - 添加 LiteLLM Proxy 启动逻辑
- ✅ `stop_all.sh` - 添加 LiteLLM Proxy 停止逻辑

### 代码文件
- ✅ `web/backend/agent_generation.py` - 配置使用 LiteLLM Proxy

### 环境变量 (.env)
自动添加：
```bash
LITELLM_MASTER_KEY=sk-litellm-xxxxx
ANTHROPIC_BASE_URL=http://0.0.0.0:4000
ANTHROPIC_AUTH_TOKEN=${LITELLM_MASTER_KEY}
ANTHROPIC_MODEL=openrouter/deepseek/deepseek-v3.1-terminus-v3-0324
```

## 总结

运行 `./start_all_with_agent.sh` 会：

1. ✅ 自动生成 `LITELLM_MASTER_KEY`
2. ✅ 配置 Claude Agent SDK 环境变量
3. ✅ 启动 LiteLLM Proxy (DeepSeek 模型)
4. ✅ 启动 FastAPI Backend
5. ✅ 启动 Next.js Frontend
6. ✅ 所有服务互联互通

**一键启动，开箱即用！** 🚀
