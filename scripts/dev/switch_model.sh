#!/bin/bash

# 模型切换脚本
# 用法: ./scripts/dev/switch_model.sh <model_name>

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# 可用模型列表
declare -A MODELS=(
    ["kimi"]="moonshotai/kimi-k2-thinking"
    ["deepseek"]="deepseek/deepseek-v3.1-terminus"
    ["claude-sonnet"]="anthropic/claude-3.5-sonnet"
    ["claude-haiku"]="anthropic/claude-3-haiku"
    ["gpt-4"]="openai/gpt-4-turbo"
    ["qwen"]="qwen/qwen-2.5-72b-instruct"
)

# 显示帮助
show_help() {
    echo -e "${BLUE}模型切换脚本${NC}"
    echo ""
    echo "用法:"
    echo "  ./scripts/dev/switch_model.sh <model_name>"
    echo ""
    echo "可用模型:"
    for key in "${!MODELS[@]}"; do
        echo -e "  ${GREEN}$key${NC} -> ${MODELS[$key]}"
    done
    echo ""
    echo "示例:"
    echo "  ./scripts/dev/switch_model.sh kimi"
    echo "  ./scripts/dev/switch_model.sh deepseek"
}

# 检查参数
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

MODEL_KEY="$1"

# 检查模型是否存在
if [ -z "${MODELS[$MODEL_KEY]}" ]; then
    echo -e "${RED}错误: 未知模型 '$MODEL_KEY'${NC}"
    echo ""
    show_help
    exit 1
fi

MODEL_FULL_NAME="${MODELS[$MODEL_KEY]}"

# 检查 .env 文件是否存在
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}错误: .env 文件不存在${NC}"
    exit 1
fi

echo -e "${BLUE}=== 模型切换 ===${NC}"
echo -e "切换到: ${GREEN}$MODEL_KEY${NC} (${MODEL_FULL_NAME})"
echo ""

# 备份 .env 文件
cp "$ENV_FILE" "$ENV_FILE.backup"
echo -e "${YELLOW}✓${NC} 已备份 .env 文件"

# 更新 DEFAULT_MODEL
if grep -q "^DEFAULT_MODEL=" "$ENV_FILE"; then
    # 替换现有行
    sed -i.tmp "s|^DEFAULT_MODEL=.*|DEFAULT_MODEL=$MODEL_FULL_NAME|" "$ENV_FILE"
    rm -f "$ENV_FILE.tmp"
else
    # 添加新行
    echo "" >> "$ENV_FILE"
    echo "DEFAULT_MODEL=$MODEL_FULL_NAME" >> "$ENV_FILE"
fi

echo -e "${YELLOW}✓${NC} 已更新 .env 文件"

# 显示当前配置
echo ""
echo -e "${BLUE}当前配置:${NC}"
grep "^DEFAULT_MODEL=" "$ENV_FILE" | sed 's/^/  /'

# 提示重启服务
echo ""
echo -e "${YELLOW}⚠️  注意: 需要重启后端服务才能生效${NC}"
echo ""
echo "重启命令:"
echo -e "  ${GREEN}./scripts/start/start_all_with_agent.sh${NC}"
echo ""
echo "或手动重启后端:"
echo -e "  ${GREEN}cd web/backend && uv run uvicorn main:app --reload --port 8000${NC}"

echo ""
echo -e "${GREEN}✅ 模型切换完成${NC}"
