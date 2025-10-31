#!/bin/bash
# Web 服务启动脚本

echo "🚀 启动 AI 小说生成器 Web 服务"
echo "=================================="

# 检查是否在项目根目录
if [ ! -f "requirements.txt" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

# 使用 uv 管理环境
echo "📦 使用 uv 管理环境..."

# 启动后端
echo ""
echo "🔧 启动 FastAPI 后端 (端口 8000)..."
cd web/backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ../..

# 等待后端启动
sleep 2

# 检查前端依赖
if [ ! -d "web/frontend/node_modules" ]; then
    echo ""
    echo "📦 安装前端依赖..."
    cd web/frontend
    npm install
    cd ../..
fi

# 启动前端
echo ""
echo "🎨 启动 Next.js 前端 (端口 3000)..."
cd web/frontend
npm run dev &
FRONTEND_PID=$!
cd ../..

echo ""
echo "=================================="
echo "✅ 服务已启动!"
echo ""
echo "📍 后端 API: http://localhost:8000"
echo "📍 前端界面: http://localhost:3000"
echo "📍 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=================================="

# 等待用户中断
wait $BACKEND_PID $FRONTEND_PID
