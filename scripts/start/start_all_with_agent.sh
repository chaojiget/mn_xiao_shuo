#!/bin/bash

# 一键启动完整的 AI 小说生成系统
# 基于 LangChain 1.0 + OpenRouter

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 启动 AI 跑团小说系统（LangChain 1.0版本）"
echo "=============================================="
echo "项目根目录: $PROJECT_ROOT"
echo ""
echo "✨ 本次启动包含:"
echo "   • LangChain 1.0 Agent 系统"
echo "   • 15个游戏工具（LangChain @tool）"
echo "   • Global Director (智能事件调度)"
echo "   • 游戏界面 (DM交互 + 任务 + NPC)"
echo "   • 直连 OpenRouter (无中间层)"
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

# 检查 OpenRouter 配置
if [ -z "$OPENROUTER_BASE_URL" ]; then
    export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
fi

if [ -z "$DEFAULT_MODEL" ]; then
    export DEFAULT_MODEL="deepseek/deepseek-v3.1-terminus"
fi

# 创建必要的目录
mkdir -p logs
mkdir -p .pids
mkdir -p data/sqlite

# 检查端口占用并清理
echo "🔍 检查端口占用..."
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

# 检查并安装 LangChain
echo "📦 检查 LangChain 安装..."
if ! uv pip list | grep -q langchain; then
    echo "   安装 LangChain..."
    uv pip install langchain langchain-openai langchain-community
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
echo "📍 访问地址:"
echo "   后端 API:       http://localhost:8000"
echo "   API 文档:       http://localhost:8000/docs"
echo "   前端界面:       http://localhost:3000"
echo ""
echo "🎮 快速开始:"
echo "   游戏界面:       http://localhost:3000/game/play"
echo "   聊天界面:       http://localhost:3000/chat"
echo "   世界管理:       http://localhost:3000/world"
echo ""
echo "🧪 测试 LangChain Agent:"
echo "   python examples/langchain_agent_demo.py"
echo ""
echo "🤖 LangChain 配置:"
echo "   OpenRouter URL: $OPENROUTER_BASE_URL"
echo "   Default Model:  $DEFAULT_MODEL"
echo ""
echo "📊 进程 ID:"
echo "   Backend:  $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "📝 日志文件:"
echo "   logs/backend.log   (FastAPI + LangChain Agent)"
echo "   logs/frontend.log  (Next.js)"
echo ""
echo "🛑 停止所有服务:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   或运行: ./scripts/start/stop_all.sh"
echo ""
echo "📚 查看文档:"
echo "   docs/implementation/LANGCHAIN_MIGRATION_PLAN.md  (迁移计划)"
echo "   docs/features/GAME_UI_GUIDE.md                   (游戏界面指南)"
echo "=============================================="

# 保存 PID 到文件
echo "$BACKEND_PID" > .pids/backend.pid
echo "$FRONTEND_PID" > .pids/frontend.pid

# 等待用户中断
echo ""
echo "按 Ctrl+C 停止所有服务..."
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo ''; echo '✅ 所有服务已停止'" INT TERM
wait
