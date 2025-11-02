#!/bin/bash

# 停止所有服务（包括 LiteLLM Proxy）

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🛑 停止 AI 跑团小说系统..."
echo "================================"

# 从 PID 文件读取进程 ID
if [ -f .pids/litellm.pid ]; then
    LITELLM_PID=$(cat .pids/litellm.pid)
    echo "停止 LiteLLM Proxy (PID: $LITELLM_PID)..."
    kill $LITELLM_PID 2>/dev/null && echo "  ✅ 已停止" || echo "  ⚠️  进程不存在"
fi

if [ -f .pids/backend.pid ]; then
    BACKEND_PID=$(cat .pids/backend.pid)
    echo "停止 Backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null && echo "  ✅ 已停止" || echo "  ⚠️  进程不存在"
fi

if [ -f .pids/frontend.pid ]; then
    FRONTEND_PID=$(cat .pids/frontend.pid)
    echo "停止 Frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null && echo "  ✅ 已停止" || echo "  ⚠️  进程不存在"
fi

# 清理 PID 文件
rm -f .pids/*.pid

# 额外保险: 杀死占用端口的进程
echo ""
echo "检查端口占用..."
lsof -ti:4000 | xargs kill -9 2>/dev/null && echo "  端口 4000 (LiteLLM) 已清理" || true
lsof -ti:8000 | xargs kill -9 2>/dev/null && echo "  端口 8000 (Backend) 已清理" || true
lsof -ti:3000 | xargs kill -9 2>/dev/null && echo "  端口 3000 (Frontend) 已清理" || true

# 杀死所有 litellm 进程（以防万一）
pkill -f litellm 2>/dev/null && echo "  已清理所有 litellm 进程" || true

echo ""
echo "✅ 所有服务已停止"
echo "================================"
