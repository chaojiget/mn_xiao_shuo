#!/bin/bash

# 检查所有服务状态

echo "🔍 检查服务状态..."
echo "=========================================="

# 检查 LiteLLM Proxy
echo ""
echo "1️⃣  LiteLLM Proxy (端口 4000):"
if lsof -ti:4000 > /dev/null 2>&1; then
    PID=$(lsof -ti:4000)
    echo "   ✅ 运行中 (PID: $PID)"

    # 测试 API
    if curl -s http://localhost:4000/v1/models > /dev/null 2>&1; then
        echo "   ✅ API 响应正常"
    else
        echo "   ⚠️  API 无响应"
    fi
else
    echo "   ❌ 未运行"
fi

# 检查 Backend
echo ""
echo "2️⃣  FastAPI Backend (端口 8000):"
if lsof -ti:8000 > /dev/null 2>&1; then
    PID=$(lsof -ti:8000)
    echo "   ✅ 运行中 (PID: $PID)"

    # 测试 API
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo "   ✅ API 响应正常"
        echo "   📍 API 文档: http://localhost:8000/docs"
    else
        echo "   ⚠️  API 无响应"
    fi
else
    echo "   ❌ 未运行"
fi

# 检查 Frontend
echo ""
echo "3️⃣  Next.js Frontend (端口 3000):"
if lsof -ti:3000 > /dev/null 2>&1; then
    PID=$(lsof -ti:3000)
    echo "   ✅ 运行中 (PID: $PID)"
    echo "   📍 前端界面: http://localhost:3000"
else
    echo "   ❌ 未运行"
fi

# 检查环境变量
echo ""
echo "4️⃣  环境变量:"
if [ -n "$LITELLM_MASTER_KEY" ]; then
    echo "   ✅ LITELLM_MASTER_KEY: ${LITELLM_MASTER_KEY:0:20}..."
else
    echo "   ⚠️  LITELLM_MASTER_KEY 未设置"
fi

if [ -n "$ANTHROPIC_BASE_URL" ]; then
    echo "   ✅ ANTHROPIC_BASE_URL: $ANTHROPIC_BASE_URL"
else
    echo "   ⚠️  ANTHROPIC_BASE_URL 未设置"
fi

if [ -n "$ANTHROPIC_MODEL" ]; then
    echo "   ✅ ANTHROPIC_MODEL: $ANTHROPIC_MODEL"
else
    echo "   ⚠️  ANTHROPIC_MODEL 未设置"
fi

# 检查日志文件
echo ""
echo "5️⃣  日志文件:"
if [ -f logs/litellm.log ]; then
    LINES=$(wc -l < logs/litellm.log)
    echo "   📝 logs/litellm.log ($LINES 行)"

    # 检查最近的错误
    if grep -i "error" logs/litellm.log | tail -1 > /dev/null 2>&1; then
        echo "   ⚠️  发现错误，最后一行:"
        grep -i "error" logs/litellm.log | tail -1 | sed 's/^/      /'
    fi
fi

if [ -f logs/backend.log ]; then
    LINES=$(wc -l < logs/backend.log)
    echo "   📝 logs/backend.log ($LINES 行)"

    # 检查最近的错误
    if grep -i "error" logs/backend.log | tail -1 > /dev/null 2>&1; then
        echo "   ⚠️  发现错误，最后一行:"
        grep -i "error" logs/backend.log | tail -1 | sed 's/^/      /'
    fi
fi

if [ -f logs/frontend.log ]; then
    LINES=$(wc -l < logs/frontend.log)
    echo "   📝 logs/frontend.log ($LINES 行)"
fi

echo ""
echo "=========================================="
echo "💡 提示:"
echo "   查看完整日志: tail -f logs/*.log"
echo "   停止所有服务: ./stop_all.sh"
echo "=========================================="
