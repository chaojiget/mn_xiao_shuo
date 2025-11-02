#!/bin/bash

# LiteLLM Proxy 端到端测试脚本

cd "$(dirname "$0")"
source .venv/bin/activate

echo "========================================="
echo "🧪 LiteLLM Proxy 端到端测试"
echo "========================================="
echo ""

# 1. 检查 LiteLLM Proxy 是否在运行
echo "1️⃣  检查 LiteLLM Proxy 状态..."
if curl -s http://localhost:4000/health > /dev/null 2>&1; then
    echo "   ✅ LiteLLM Proxy 正在运行 (http://localhost:4000)"
else
    echo "   ❌ LiteLLM Proxy 未运行"
    echo "   请先运行: ./start_litellm_proxy.sh"
    exit 1
fi

# 2. 检查环境变量
echo ""
echo "2️⃣  检查环境变量..."
if [ -z "$LITELLM_MASTER_KEY" ]; then
    # 从 .env 读取
    if grep -q "LITELLM_MASTER_KEY" .env 2>/dev/null; then
        export LITELLM_MASTER_KEY=$(grep LITELLM_MASTER_KEY .env | cut -d '=' -f2-)
        echo "   ✅ LITELLM_MASTER_KEY: $LITELLM_MASTER_KEY (从 .env 读取)"
    else
        echo "   ❌ LITELLM_MASTER_KEY 未设置"
        exit 1
    fi
else
    echo "   ✅ LITELLM_MASTER_KEY: $LITELLM_MASTER_KEY"
fi

# 3. 测试 API 调用
echo ""
echo "3️⃣  测试 API 调用..."
python test_litellm_api.py

echo ""
echo "========================================="
echo "测试完成！"
echo "========================================="
