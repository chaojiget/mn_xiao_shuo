#!/bin/bash

# 一键启动完整的 AI 小说生成系统
# 包括: LiteLLM Proxy + FastAPI Backend + Next.js Frontend

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 启动 AI 跑团小说系统（完整版）"
echo "=============================================="
echo "项目根目录: $PROJECT_ROOT"
echo ""

# 激活虚拟环境
source .venv/bin/activate

# 加载 .env 文件
if [ -f .env ]; then
    echo "📝 加载环境变量..."
    # 使用 source 或 set -a 加载环境变量
    set -a
    source .env
    set +a
else
    echo "❌ 错误: .env 文件不存在"
    echo "   请复制 .env.example 到 .env 并设置必要的环境变量"
    exit 1
fi

# 检查环境变量
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ 错误: OPENROUTER_API_KEY 未设置"
    echo "   请在 .env 文件中设置 OPENROUTER_API_KEY"
    exit 1
fi

# 生成或读取 LITELLM_MASTER_KEY
if [ -z "$LITELLM_MASTER_KEY" ]; then
    echo "🔑 生成 LITELLM_MASTER_KEY..."
    export LITELLM_MASTER_KEY="sk-litellm-$(openssl rand -hex 16)"

    # 检查 .env 中是否已有 LITELLM_MASTER_KEY
    if ! grep -q "LITELLM_MASTER_KEY" .env 2>/dev/null; then
        echo "" >> .env
        echo "# LiteLLM Proxy 认证" >> .env
        echo "LITELLM_MASTER_KEY=$LITELLM_MASTER_KEY" >> .env
        echo ""
        echo "# Claude Agent SDK 环境变量（使用 LiteLLM Proxy）" >> .env
        echo "ANTHROPIC_BASE_URL=http://0.0.0.0:4000" >> .env
        echo "ANTHROPIC_AUTH_TOKEN=\${LITELLM_MASTER_KEY}" >> .env
        echo "ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324" >> .env
        echo "✅ 已保存 LITELLM_MASTER_KEY 到 .env"
    fi
fi

# 设置 Claude Agent SDK 环境变量
export ANTHROPIC_BASE_URL="http://0.0.0.0:4000"
export ANTHROPIC_AUTH_TOKEN="$LITELLM_MASTER_KEY"
export ANTHROPIC_MODEL="openrouter/deepseek/deepseek-chat-v3-0324"

# 创建必要的目录
mkdir -p logs
mkdir -p .pids
mkdir -p data/sqlite

# 检查端口占用并清理
echo "🔍 检查端口占用..."
if lsof -ti:4000 > /dev/null 2>&1; then
    echo "   端口 4000 被占用，正在清理..."
    lsof -ti:4000 | xargs kill -9 2>/dev/null
    sleep 1
fi
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "   端口 8000 被占用，正在清理..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi
if lsof -ti:3000 > /dev/null 2>&1; then
    echo "   端口 3000 被占用，正在清理..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# 检查并安装 LiteLLM Proxy
echo "📦 检查 LiteLLM Proxy 安装..."
if ! uv pip list | grep -q litellm; then
    echo "   安装 LiteLLM Proxy..."
    uv pip install 'litellm[proxy]'
fi

# 启动 LiteLLM Proxy (端口 4000)
echo "🤖 启动 LiteLLM Proxy (端口 4000)..."
litellm --config ./config/litellm_config.yaml --host 0.0.0.0 --port 4000 > logs/litellm.log 2>&1 &
LITELLM_PID=$!
echo "   PID: $LITELLM_PID"

# 等待 LiteLLM Proxy 启动
echo "⏳ 等待 LiteLLM Proxy 启动..."
sleep 5

# 检查 LiteLLM Proxy 是否正常（使用 v1/models 端点，不需要认证）
if curl -s http://localhost:4000/v1/models > /dev/null 2>&1; then
    echo "✅ LiteLLM Proxy 启动成功"
else
    echo "⚠️  LiteLLM Proxy 可能仍在启动中"
fi

# 启动后端（环境变量已从 .env 加载）
echo "🔧 启动 FastAPI 后端 (端口 8000)..."
cd web/backend
# 使用 .venv 中的 uvicorn 而不是 uv run，确保环境变量传递
../../.venv/bin/uvicorn main:app --reload --port 8000 > ../../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"
cd ../..

# 等待后端启动
echo "⏳ 等待后端启动..."
sleep 3

# 检查后端是否正常
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端启动成功"
else
    echo "⚠️  后端可能仍在启动中,请稍后访问 http://localhost:8000/docs"
fi

# 启动前端
echo "🎨 启动 Next.js 前端 (端口 3000)..."
cd web/frontend
npm run dev > ../../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   PID: $FRONTEND_PID"
cd ../..

echo ""
echo "=============================================="
echo "✅ 所有服务已启动！"
echo ""
echo "📍 LiteLLM Proxy:  http://localhost:4000"
echo "📍 后端 API:       http://localhost:8000"
echo "📍 API 文档:       http://localhost:8000/docs"
echo "📍 前端界面:       http://localhost:3000"
echo ""
echo "🤖 Claude Agent SDK 配置:"
echo "   ANTHROPIC_BASE_URL=$ANTHROPIC_BASE_URL"
echo "   ANTHROPIC_MODEL=$ANTHROPIC_MODEL"
echo ""
echo "📊 进程 ID:"
echo "   LiteLLM Proxy: $LITELLM_PID"
echo "   Backend:       $BACKEND_PID"
echo "   Frontend:      $FRONTEND_PID"
echo ""
echo "📝 日志文件:"
echo "   logs/litellm.log"
echo "   logs/backend.log"
echo "   logs/frontend.log"
echo ""
echo "🛑 停止所有服务:"
echo "   kill $LITELLM_PID $BACKEND_PID $FRONTEND_PID"
echo "   或运行: ./stop_all.sh"
echo "=============================================="

# 保存 PID 到文件
echo "$LITELLM_PID" > .pids/litellm.pid
echo "$BACKEND_PID" > .pids/backend.pid
echo "$FRONTEND_PID" > .pids/frontend.pid

# 等待用户中断
echo ""
echo "按 Ctrl+C 停止所有服务..."
trap "kill $LITELLM_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo ''; echo '✅ 所有服务已停止'" INT TERM
wait
