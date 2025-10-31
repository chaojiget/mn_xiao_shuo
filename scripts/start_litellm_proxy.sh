#!/bin/bash

# 启动 LiteLLM Proxy Server
# 这个代理服务器会提供 Anthropic 兼容的 API，但实际使用 DeepSeek

echo "🚀 启动 LiteLLM Proxy Server (路由到 DeepSeek)"
echo "================================================"

# 加载环境变量
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# 检查环境变量
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ 错误: OPENROUTER_API_KEY 未设置"
    echo "请在 .env 文件中设置"
    exit 1
fi

# 启动代理服务器 (使用 uv)
uv run litellm --config config/litellm_proxy_config.yaml --port 4000

# 使用说明:
# 1. Proxy 运行在 http://localhost:4000
# 2. 设置环境变量:
#    export ANTHROPIC_API_BASE=http://localhost:4000
#    export ANTHROPIC_API_KEY=sk-fake-key  # 任意值
# 3. Claude Agent SDK 会使用这个代理，实际调用 DeepSeek
