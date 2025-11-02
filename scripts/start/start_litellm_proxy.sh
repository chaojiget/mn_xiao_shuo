#!/bin/bash

# 启动 LiteLLM 代理服务器
# 这个脚本会在 http://0.0.0.0:4000 启动 LiteLLM 代理

cd "$(dirname "$0")"

# 激活虚拟环境
source .venv/bin/activate

# 检查是否已安装 litellm[proxy]
echo "检查 LiteLLM Proxy 安装..."
uv pip list | grep litellm || {
    echo "安装 LiteLLM Proxy..."
    uv pip install 'litellm[proxy]'
}

# 从 .env 文件读取或生成 LITELLM_MASTER_KEY
if grep -q "LITELLM_MASTER_KEY" .env 2>/dev/null; then
    export LITELLM_MASTER_KEY=$(grep LITELLM_MASTER_KEY .env | cut -d '=' -f2-)
    echo "使用现有的 LITELLM_MASTER_KEY"
else
    # 生成一个简单的 master key
    export LITELLM_MASTER_KEY="sk-litellm-$(openssl rand -hex 16)"
    echo "" >> .env
    echo "# LiteLLM Proxy 认证" >> .env
    echo "LITELLM_MASTER_KEY=$LITELLM_MASTER_KEY" >> .env
    echo ""
    echo "# Claude Agent SDK 环境变量（使用 LiteLLM Proxy）" >> .env
    echo "ANTHROPIC_BASE_URL=http://0.0.0.0:4000" >> .env
    echo "ANTHROPIC_AUTH_TOKEN=\${LITELLM_MASTER_KEY}" >> .env
    echo "ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324" >> .env
    echo ""
    echo "✅ 已生成并保存配置到 .env 文件："
    echo "   LITELLM_MASTER_KEY=$LITELLM_MASTER_KEY"
    echo "   ANTHROPIC_BASE_URL=http://0.0.0.0:4000"
    echo "   ANTHROPIC_AUTH_TOKEN=\${LITELLM_MASTER_KEY}"
    echo "   ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324"
    echo ""
fi

# 导出 Claude Agent SDK 环境变量
export ANTHROPIC_BASE_URL="http://0.0.0.0:4000"
export ANTHROPIC_AUTH_TOKEN="$LITELLM_MASTER_KEY"
export ANTHROPIC_MODEL="openrouter/deepseek/deepseek-chat-v3-0324"

# 设置 OpenRouter API Key (从 .env 读取)
if [ -f .env ]; then
    export OPENROUTER_API_KEY=$(grep OPENROUTER_API_KEY .env | cut -d '=' -f2-)
fi

echo "==========================================="
echo "🚀 LiteLLM 代理服务器启动中..."
echo "==========================================="
echo "配置文件: ./config/litellm_config.yaml"
echo "监听地址: http://0.0.0.0:4000"
echo "Master Key: $LITELLM_MASTER_KEY"
echo ""
echo "📝 可用的模型别名："
echo "   - deepseek          (openrouter/deepseek/deepseek-chat-v3-0324)"
echo "   - claude-sonnet     (openrouter/anthropic/claude-sonnet-4.5)"
echo "   - claude-haiku      (openrouter/anthropic/claude-3.5-haiku)"
echo "   - gpt-4             (openrouter/openai/gpt-4-turbo)"
echo "   - qwen              (openrouter/qwen/qwen-2.5-72b-instruct)"
echo ""
echo "🤖 Claude Agent SDK 配置（已自动设置）："
echo "   ANTHROPIC_BASE_URL=$ANTHROPIC_BASE_URL"
echo "   ANTHROPIC_AUTH_TOKEN=$ANTHROPIC_AUTH_TOKEN"
echo "   ANTHROPIC_MODEL=$ANTHROPIC_MODEL"
echo ""
echo "💡 Claude Agent SDK 现在会自动使用 LiteLLM Proxy 和 DeepSeek 模型"
echo ""
echo "🧪 测试命令："
echo "   curl -H 'Authorization: Bearer $LITELLM_MASTER_KEY' http://localhost:4000/v1/models"
echo ""
echo "⏹️  按 Ctrl+C 停止服务器"
echo "==========================================="
echo ""

# 启动 LiteLLM 代理
# 使用 --host 0.0.0.0 允许外部访问
litellm --config ./config/litellm_config.yaml --host 0.0.0.0 --port 4000
