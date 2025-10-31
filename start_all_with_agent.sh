#!/bin/bash

# 一键启动完整的 AI 小说生成系统
# 包括: FastAPI Backend + Next.js Frontend
# 注意: 不需要 LiteLLM Proxy,后端直接使用 LiteLLM Client

echo "🚀 启动 AI 跑团小说系统"
echo "=============================================="

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

# 创建必要的目录
mkdir -p logs
mkdir -p .pids
mkdir -p data/sqlite

# 启动后端（环境变量已从 .env 加载）
echo "🔧 启动 FastAPI 后端 (端口 8000)..."
cd web/backend
uv run uvicorn main:app --reload --port 8000 > ../../logs/backend.log 2>&1 &
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
echo "📍 后端 API:       http://localhost:8000"
echo "📍 API 文档:       http://localhost:8000/docs"
echo "📍 前端界面:       http://localhost:3000"
echo ""
echo "📊 进程 ID:"
echo "   Backend:       $BACKEND_PID"
echo "   Frontend:      $FRONTEND_PID"
echo ""
echo "📝 日志文件:"
echo "   logs/backend.log"
echo "   logs/frontend.log"
echo ""
echo "🛑 停止所有服务:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   或运行: ./stop_all.sh"
echo "=============================================="

# 保存 PID 到文件
echo "$BACKEND_PID" > .pids/backend.pid
echo "$FRONTEND_PID" > .pids/frontend.pid

# 等待用户中断
echo ""
echo "按 Ctrl+C 停止所有服务..."
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo ''; echo '✅ 所有服务已停止'" INT TERM
wait
